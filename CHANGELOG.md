# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### /feat - Initial FastAPI backend service
- Created FastAPI application with PostgreSQL database integration
- Added SQLAlchemy models for expense data
- Implemented CSV upload route to read and store expenses from CSV files
- Added route to read default mock.csv file and store in database
- Created database schema with all expense fields (transaction_id, amount, currency, datetime, payment_method, etc.)
- Added endpoints for listing and retrieving expenses
- Configured PostgreSQL connection with password "admin"

### /chore - Environment variables configuration
- Updated database configuration to use .env file with load_dotenv()
- Added support for individual database environment variables (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
- Created .env file with default database configuration
- Added python-dotenv dependency to requirements.txt

### /feat - Hello world route and unit tests
- Added GET /hello endpoint that returns "Hello, World!" message
- Created comprehensive unit tests using pytest with mock.csv as test data
- Added test suite covering all API endpoints (hello, CSV upload, expense retrieval, pagination)
- Tests use in-memory SQLite database for fast test execution
- Added pytest and httpx dependencies for testing

### /fix - Test database connection issues
- Fixed database connection errors in tests by overriding PostgreSQL engine with SQLite in-memory engine
- Tests now properly isolate database connections and don't require PostgreSQL during test execution
- Fixed test data type assertions to handle Decimal serialization properly

### /chore - Database authentication defaults
- Added default values for database connection (user: postgres, password: admin)
- Database configuration now defaults to postgres/admin if .env file is missing or incomplete
- Ensures consistent authentication credentials across environments

### /feat - Database query endpoint
- Added GET /api/expenses/query/database endpoint to query and filter expenses from database
- Supports filtering by department, expense_type, vendor_name, currency, amount range, and date range
- Includes pagination support with skip and limit parameters
- Returns expenses ordered by datetime (most recent first)

### /feat - User authentication and authorization
- Added User model with email/password authentication
- Implemented JWT-based authentication system
- Added login and registration endpoints (/api/auth/login, /api/auth/register)
- Updated Expense model to relate to User (user_id foreign key)
- Made transaction_id unique per user (not globally unique)
- All expense endpoints now require authentication
- Expenses are automatically filtered by authenticated user
- Added password hashing using bcrypt directly (bypassed passlib compatibility issues)
- Added temporary database wipe script (wipe_db.py)

### /fix - Updated tests for authentication and bcrypt compatibility
- Updated all unit tests to include authentication fixtures and test authenticated endpoints
- Added comprehensive auth endpoint tests (register, login, duplicate email, wrong password)
- Added user isolation test to verify expenses are properly filtered by user
- Fixed bcrypt compatibility issue by using bcrypt library directly instead of passlib wrapper
- Fixed datetime default values in models to use lambda functions for proper SQLAlchemy compatibility
- All 20 tests now pass successfully
- Added email-validator dependency for Pydantic EmailStr validation

### /feat - Frontend-backend integration with login system
- Integrated React frontend with FastAPI backend authentication system
- Created AuthContext to manage authentication state across the application
- Implemented Login component with form validation and error handling
- Implemented Register component with user registration functionality
- Updated App.jsx to handle authentication flow and protect routes
- Updated LandingPage to integrate with backend API for CSV upload
- Updated LandingPage to support loading default CSV from backend
- Added logout functionality to both LandingPage and Dashboard components
- All API requests now include JWT authentication tokens
- Frontend now properly handles authentication state and redirects unauthenticated users

### /feat - Request logging middleware with POST data
- Added RequestLoggingMiddleware to log all incoming HTTP requests
- Logs request method, path, client IP, query parameters, and POST body data
- Supports logging JSON, form-urlencoded, and multipart form data
- Masks sensitive data: passwords in request bodies and JWT tokens in headers
- Logs request processing time and response status codes
- Logs errors with full context for debugging
- Configured logging to output to stdout with timestamps and log levels
- Logs detailed body data at INFO level, full request details at DEBUG level

### /feat - Background CSV processing and user data check on login
- Updated CSV upload endpoint to use FastAPI BackgroundTasks for asynchronous processing
- CSV processing now runs in background to avoid blocking frontend requests
- Created process_csv_data helper function that creates its own database session for background processing
- Updated read_default_csv endpoint to also use background processing
- Login endpoint now checks if user has existing expenses and returns has_data flag in response
- Frontend automatically checks for user data on login and redirects accordingly
- Users with existing data are automatically redirected to dashboard with their data loaded
- Users without data are redirected to CSV upload page
- Frontend automatically loads user expense data when authenticated user has expenses
- Updated AuthContext to track hasData state and provide refreshDataStatus function

