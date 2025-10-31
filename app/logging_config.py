import logging
import sys
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests with POST data"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get request method and path
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        
        # Read request body for POST/PUT/PATCH requests
        body_data = None
        body_bytes = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    # Check if it's JSON
                    try:
                        body_data = json.loads(body_bytes.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If not JSON, check content type
                        content_type = request.headers.get("content-type", "")
                        if "application/x-www-form-urlencoded" in content_type:
                            # Form data - parse it for better logging
                            try:
                                from urllib.parse import parse_qs
                                decoded = body_bytes.decode('utf-8')
                                parsed_form = parse_qs(decoded)
                                # Convert parse_qs result (lists) to dict with first value
                                body_data = {k: v[0] if len(v) == 1 else v for k, v in parsed_form.items()}
                            except Exception:
                                try:
                                    body_data = body_bytes.decode('utf-8')
                                except UnicodeDecodeError:
                                    body_data = f"<form data, size: {len(body_bytes)} bytes>"
                        elif "multipart/form-data" in content_type:
                            # File upload - don't log the actual file content
                            body_data = f"<multipart form data, size: {len(body_bytes)} bytes>"
                        else:
                            # Try to decode as text
                            try:
                                body_data = body_bytes.decode('utf-8')
                            except UnicodeDecodeError:
                                # Binary data
                                body_data = f"<binary data, size: {len(body_bytes)} bytes>"
            except Exception as e:
                body_data = f"<error reading body: {str(e)}>"
        
        # Recreate request with body for downstream processing
        # Since FastAPI consumes the body, we need to make it available again
        if body_bytes is not None:
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            
            # Replace the request's receive function to make body available again
            request._receive = receive
        
        # Log request details
        log_data = {
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "query_params": query_params if query_params else None,
            "headers": dict(request.headers),
            "body": body_data
        }
        
        # Mask sensitive data in headers
        if "authorization" in log_data["headers"]:
            auth_header = log_data["headers"]["authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                if len(token) > 10:
                    masked_token = token[:4] + "..." + token[-4:]
                    log_data["headers"]["authorization"] = f"Bearer {masked_token}"
        
        # Mask sensitive data in body (passwords) for logging
        safe_body = body_data
        if isinstance(body_data, dict):
            safe_body = body_data.copy()
            if "password" in safe_body:
                safe_body["password"] = "***MASKED***"
            if "hashed_password" in safe_body:
                safe_body["hashed_password"] = "***MASKED***"
        
        log_data["body"] = safe_body
        
        # Log the request
        logger.info(f"Request: {method} {path} from {client_ip}")
        
        # Log query parameters if present
        if query_params:
            logger.info(f"  Query params: {query_params}")
        
        # Log body data if present (using safe_body to mask passwords)
        if safe_body is not None:
            if isinstance(safe_body, dict):
                logger.info(f"  Body (JSON): {json.dumps(safe_body, indent=2, default=str)}")
            elif isinstance(safe_body, str):
                # Limit string length for readability
                body_preview = safe_body[:500] + "..." if len(safe_body) > 500 else safe_body
                logger.info(f"  Body: {body_preview}")
            else:
                logger.info(f"  Body: {safe_body}")
        
        # Log full details at debug level
        logger.debug(f"Full request details: {json.dumps(log_data, indent=2, default=str)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate process time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {method} {path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error processing {method} {path}: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            raise

