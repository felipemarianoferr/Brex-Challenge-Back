from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import csv
import io
from datetime import datetime
from decimal import Decimal

from app.database import get_db, init_db
from app.models import Expense
from app.schemas import ExpenseResponse, CSVUploadResponse

app = FastAPI(
    title="Tech Startup Expenses API",
    description="API to manage and store tech startup expenses from CSV files",
    version="1.0.0"
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


@app.post("/api/expenses/upload-csv", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a CSV file containing expenses.
    The CSV will be parsed and stored in the PostgreSQL database.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    try:
        # Read CSV content
        contents = await file.read()
        csv_content = contents.decode('utf-8')
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

            # Check if expense already exists
            existing_expense = db.query(Expense).filter(
                Expense.transaction_id == row['transaction_id'].strip()
            ).first()

            # Prepare expense data
            expense_data = {
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
                    setattr(existing_expense, key, value)
                records_updated += 1
            else:
                # Create new expense
                new_expense = Expense(**expense_data)
                db.add(new_expense)
                records_inserted += 1

        # Commit all changes
        db.commit()

        return CSVUploadResponse(
            message="CSV processed successfully",
            records_processed=records_processed,
            records_inserted=records_inserted,
            records_updated=records_updated
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing CSV: {str(e)}"
        )


@app.get("/api/expenses", response_model=List[ExpenseResponse])
async def list_expenses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all expenses with pagination.
    """
    expenses = db.query(Expense).offset(skip).limit(limit).all()
    return expenses


@app.get("/api/expenses/{transaction_id}", response_model=ExpenseResponse)
async def get_expense(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific expense by transaction_id.
    """
    expense = db.query(Expense).filter(
        Expense.transaction_id == transaction_id
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
    db: Session = Depends(get_db)
):
    """
    Query and read expenses from the database with various filters.
    
    Supports filtering by:
    - department
    - expense_type
    - vendor_name
    - currency
    - amount range (min_amount, max_amount)
    - date range (start_date, end_date)
    """
    db_query = db.query(Expense)
    
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
async def read_default_csv(db: Session = Depends(get_db)):
    """
    Read the default mock.csv file and store data in the database.
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
            csv_reader = csv.DictReader(file)

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

                # Check if expense already exists
                existing_expense = db.query(Expense).filter(
                    Expense.transaction_id == row['transaction_id'].strip()
                ).first()

                # Prepare expense data
                expense_data = {
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
                        setattr(existing_expense, key, value)
                    records_updated += 1
                else:
                    # Create new expense
                    new_expense = Expense(**expense_data)
                    db.add(new_expense)
                    records_inserted += 1

            # Commit all changes
            db.commit()

            return CSVUploadResponse(
                message="CSV processed successfully",
                records_processed=records_processed,
                records_inserted=records_inserted,
                records_updated=records_updated
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing CSV: {str(e)}"
        )

