# Brex-Challenge-Back

A FastAPI backend service for managing tech startup expenses from CSV files.

## Features

- Read and parse CSV files containing expense data
- Store expenses in PostgreSQL database
- RESTful API endpoints for managing expenses
- Automatic database schema creation

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## Setup

1. **Install PostgreSQL** (if not already installed)
   - Make sure PostgreSQL is running on localhost:5432
   - Default database user: `postgres`
   - Default password: `admin` (as specified in the project)

2. **Create a database**
   ```sql
   CREATE DATABASE expenses_db;
   ```

3. **Clone the repository and navigate to the project directory**

4. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   ```

5. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

6. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The database connection is configured via environment variables in a `.env` file. Create a `.env` file in the project root with the following variables:

```env
DB_USER=postgres
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=5432
DB_NAME=expenses_db
```

The application automatically loads these variables using `python-dotenv`. You can modify the `.env` file to match your PostgreSQL configuration.

## Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

## API Endpoints

### Root
- `GET /` - API information and available endpoints

### Expenses

- `POST /api/expenses/upload-csv` - Upload a CSV file to import expenses
  - Accepts a CSV file via form-data
  - Returns summary of processed records

- `POST /api/expenses/read-default-csv` - Read the default `mock.csv` file and store expenses
  - Reads the `mock.csv` file from the project root
  - Returns summary of processed records

- `GET /api/expenses` - List all expenses (with pagination)
  - Query parameters: `skip` (default: 0), `limit` (default: 100)

- `GET /api/expenses/{transaction_id}` - Get a specific expense by transaction_id

## CSV Format

The CSV file should have the following columns:
- `transaction_id` - Unique identifier for the transaction
- `amount` - Transaction amount (decimal)
- `currency` - Currency code (e.g., USD)
- `datetime` - Transaction datetime (format: YYYY-MM-DD HH:MM:SS)
- `payment_method` - Payment method (e.g., TED, PIX, WIRE)
- `src_account` - Source account
- `dst_account` - Destination account
- `vendor_name` - Vendor name
- `start_date` - Start date (format: YYYY-MM-DD)
- `end_date` - End date (format: YYYY-MM-DD)
- `recurrency` - Recurrence pattern (e.g., Monthly, Quarterly)
- `department` - Department name
- `expense_type` - Type of expense (e.g., subscriptions, rent)
- `expense_name` - Name/description of the expense

## Running Tests

Run the test suite using pytest:

```bash
pytest tests/
```

Run tests with verbose output:

```bash
pytest tests/ -v
```

The tests use an in-memory SQLite database for fast execution and use the `mock.csv` file as test data.

## Example Usage

### Hello World Route
```bash
curl "http://localhost:8000/hello"
```

### Read default CSV file
```bash
curl -X POST "http://localhost:8000/api/expenses/read-default-csv"
```

### Upload a CSV file
```bash
curl -X POST "http://localhost:8000/api/expenses/upload-csv" \
  -F "file=@path/to/your/expenses.csv"
```

### List all expenses
```bash
curl "http://localhost:8000/api/expenses"
```

### Get a specific expense
```bash
curl "http://localhost:8000/api/expenses/T0001"
```

## Project Structure

```
Brex-Challenge-Back/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and routes
│   ├── models.py        # SQLAlchemy database models
│   ├── schemas.py       # Pydantic schemas for request/response
│   └── database.py      # Database configuration and session
├── mock.csv             # Sample expense data
├── requirements.txt     # Python dependencies
├── tests/               # Test suite
│   ├── __init__.py
│   └── test_main.py     # Unit tests for API endpoints
├── .gitignore          # Git ignore rules
├── CHANGELOG.md        # Project changelog
└── README.md           # This file
```
