from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import get_db, init_db, SessionLocal
from app.models import Expense, User
from app.schemas import ExpenseResponse, CSVUploadResponse, UserCreate, UserResponse, Token
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.logging_config import RequestLoggingMiddleware


def process_csv_data(
    csv_content: str,
    user_id: UUID
):
    """
    Process CSV data and store expenses in database.
    This function runs in the background to avoid blocking the request.
    Creates its own database session for background processing.
    """
    # Create a new database session for background task
    db = SessionLocal()
    try:
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        records_processed = 0
        records_inserted = 0
        records_updated = 0
        
        # Process each row
        for row in csv_reader:
            # Skip empty rows
            if not row.get('transaction_id') or not row.get('transaction_id').strip():
                continue
            
            records_processed += 1
            
            # Parse datetime fields
            def parse_datetime(date_str):
                if not date_str or not date_str.strip():
                    return None
                try:
                    return datetime.strptime(date_str.strip(), '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        return datetime.strptime(date_str.strip(), '%Y-%m-%d')
                    except ValueError:
                        return None
            
            # Convert amount to Decimal
            try:
                amount = Decimal(row.get('amount', '0').strip())
            except (ValueError, AttributeError):
                amount = Decimal('0')
            
            # Check if expense already exists for this user
            existing_expense = db.query(Expense).filter(
                Expense.transaction_id == row['transaction_id'].strip(),
                Expense.user_id == user_id
            ).first()
            
            # Prepare expense data
            expense_data = {
                'user_id': user_id,
                'transaction_id': row['transaction_id'].strip(),
                'amount': amount,
                'currency': row.get('currency', 'USD').strip(),
                'datetime': parse_datetime(row.get('datetime')),
                'payment_method': row.get('payment_method', '').strip() or None,
                'src_account': row.get('src_account', '').strip() or None,
                'dst_account': row.get('dst_account', '').strip() or None,
                'vendor_name': row.get('vendor_name', '').strip() or None,
                'start_date': parse_datetime(row.get('start_date')),
                'end_date': parse_datetime(row.get('end_date')),
                'recurrency': row.get('recurrency', '').strip() or None,
                'department': row.get('department', '').strip() or None,
                'expense_type': row.get('expense_type', '').strip() or None,
                'expense_name': row.get('expense_name', '').strip() or None,
            }
            
            if existing_expense:
                # Update existing expense
                for key, value in expense_data.items():
                    if key != 'user_id':  # Don't update user_id
                        setattr(existing_expense, key, value)
                records_updated += 1
            else:
                # Create new expense
                new_expense = Expense(**expense_data)
                db.add(new_expense)
                records_inserted += 1
        
        # Commit all changes
        db.commit()
        
        # Note: These values are returned but not used since this runs in background
        # They're kept for potential logging/monitoring
        return {
            "records_processed": records_processed,
            "records_inserted": records_inserted,
            "records_updated": records_updated
        }
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


app = FastAPI(
    title="Tech Startup Expenses API",
    description="API to manage and store tech startup expenses from CSV files",
    version="1.0.0"
)

# Add request logging middleware (should be first to capture all requests)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    init_db()


@app.get("/")
async def root():
    return {
        "message": "Tech Startup Expenses API",
        "version": "1.0.0",
        "endpoints": {
            "register": "/api/auth/register",
            "login": "/api/auth/login",
            "upload_csv": "/api/expenses/upload-csv",
            "read_default_csv": "/api/expenses/read-default-csv",
            "list_expenses": "/api/expenses",
            "get_expense": "/api/expenses/{transaction_id}",
            "query_database": "/api/expenses/query/database"
        }
    }


@app.get("/hello")
async def hello_world():
    """Hello world route"""
    return {"message": "Hello, World!"}


# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get access token.
    Returns whether the user has existing expense data.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has existing expenses
    expense_count = db.query(Expense).filter(Expense.user_id == user.id).count()
    has_data = expense_count > 0
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "has_data": has_data}


@app.post("/api/expenses/upload-csv", response_model=CSVUploadResponse)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a CSV file containing expenses.
    The CSV will be parsed and stored in the PostgreSQL database for the authenticated user.
    Processing runs in the background to avoid blocking the request.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    try:
        # Read CSV content
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Add background task to process CSV data
        background_tasks.add_task(process_csv_data, csv_content, current_user.id)
        
        # Return immediately - processing happens in background
        return CSVUploadResponse(
            message="CSV upload accepted and will be processed in the background",
            records_processed=0,
            records_inserted=0,
            records_updated=0
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading CSV: {str(e)}"
        )


@app.get("/api/expenses", response_model=List[ExpenseResponse])
async def list_expenses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all expenses for the authenticated user with pagination.
    """
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return expenses


@app.get("/api/expenses/{transaction_id}", response_model=ExpenseResponse)
async def get_expense(
    transaction_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific expense by transaction_id for the authenticated user.
    """
    expense = db.query(Expense).filter(
        Expense.transaction_id == transaction_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=404,
            detail=f"Expense with transaction_id {transaction_id} not found"
        )

    return expense


@app.get("/api/expenses/query/database", response_model=List[ExpenseResponse])
async def query_database(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    department: Optional[str] = Query(None, description="Filter by department"),
    expense_type: Optional[str] = Query(None, description="Filter by expense type"),
    vendor_name: Optional[str] = Query(None, description="Filter by vendor name"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum amount"),
    start_date: Optional[str] = Query(None, description="Filter expenses from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter expenses until this date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Query and read expenses from the database with various filters for the authenticated user.
    
    Supports filtering by:
    - department
    - expense_type
    - vendor_name
    - currency
    - amount range (min_amount, max_amount)
    - date range (start_date, end_date)
    """
    db_query = db.query(Expense).filter(Expense.user_id == current_user.id)
    
    # Apply filters
    if department:
        db_query = db_query.filter(Expense.department.ilike(f"%{department}%"))
    
    if expense_type:
        db_query = db_query.filter(Expense.expense_type.ilike(f"%{expense_type}%"))
    
    if vendor_name:
        db_query = db_query.filter(Expense.vendor_name.ilike(f"%{vendor_name}%"))
    
    if currency:
        db_query = db_query.filter(Expense.currency == currency.upper())
    
    if min_amount is not None:
        db_query = db_query.filter(Expense.amount >= Decimal(str(min_amount)))
    
    if max_amount is not None:
        db_query = db_query.filter(Expense.amount <= Decimal(str(max_amount)))
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            db_query = db_query.filter(Expense.datetime >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # Include the entire end date (set to end of day)
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            db_query = db_query.filter(Expense.datetime <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Apply pagination
    expenses = db_query.order_by(Expense.datetime.desc()).offset(skip).limit(limit).all()
    
    return expenses


@app.post("/api/expenses/read-default-csv", response_model=CSVUploadResponse)
async def read_default_csv(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Read the default mock.csv file and store data in the database for the authenticated user.
    Processing runs in the background to avoid blocking the request.
    """
    import os
    
    csv_file_path = "mock.csv"
    
    if not os.path.exists(csv_file_path):
        raise HTTPException(
            status_code=404,
            detail=f"CSV file {csv_file_path} not found"
        )

    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_content = file.read()
        
        # Add background task to process CSV data
        background_tasks.add_task(process_csv_data, csv_content, current_user.id)
        
        # Return immediately - processing happens in background
        return CSVUploadResponse(
            message="Default CSV accepted and will be processed in the background",
            records_processed=0,
            records_inserted=0,
            records_updated=0
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading CSV: {str(e)}"
        )

