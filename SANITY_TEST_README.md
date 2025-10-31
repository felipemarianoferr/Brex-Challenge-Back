# Sanity Test Suite

This directory contains scripts to run a complete sanity test suite for the Brex Challenge Backend API.

## What the tests do:

1. **Unit Tests**: Run all pytest unit tests (`tests/test_main.py`)
2. **Server Check**: Verify the API server is running on `http://localhost:8000`
3. **Database Schema**: Ensure the database schema is initialized
4. **API Integration Test**: Run end-to-end test:
   - Create a new user
   - Login and get authentication token
   - Upload CSV file with expenses
   - Verify expenses were created

## How to Run

### On Linux/macOS or Git Bash (Windows)

Use the bash script:

```bash
./sanity_test.sh
```

Or:

```bash
bash sanity_test.sh
```

**Requirements:**
- Bash shell
- Python 3 installed
- All dependencies installed (`pip install -r requirements.txt`)
- API server running (`uvicorn app.main:app --reload`)

### On Windows (PowerShell)

Use the PowerShell script:

```powershell
.\sanity_test.ps1
```

If you get an execution policy error, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\sanity_test.ps1
```

### On Windows (Command Prompt)

Use the batch script:

```cmd
sanity_test.bat
```

Or double-click `sanity_test.bat`

## Prerequisites

Before running the sanity tests, make sure:

1. **Dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database is set up:**
   - PostgreSQL is running
   - Database `expenses_db` exists (or create it)
   - `.env` file is configured correctly

3. **API server is running:**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   Or in background:
   ```bash
   # Linux/macOS
   uvicorn app.main:app --reload > server.log 2>&1 &
   
   # Windows PowerShell
   Start-Process python -ArgumentList '-m','uvicorn','app.main:app','--reload'
   ```

## Troubleshooting

### Server not running

If you see an error about the server not running:

```bash
# Start the server in a separate terminal
uvicorn app.main:app --reload
```

### Database connection errors

Make sure PostgreSQL is running and the `.env` file has correct credentials:

```env
DB_USER=postgres
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=5432
DB_NAME=expenses_db
```

### Dependencies missing

Install all required dependencies:

```bash
pip install -r requirements.txt
```

### Permission errors (Linux/macOS)

Make the script executable:

```bash
chmod +x sanity_test.sh
```

### PowerShell execution policy (Windows)

If PowerShell blocks the script, allow execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Expected Output

When all tests pass, you should see:

```
============================================================
Brex Challenge Backend - Sanity Test Suite
============================================================

[STEP 1] Checking dependencies...
[OK] Dependencies are installed

[STEP 2] Running unit tests...
[OK] All unit tests passed

[STEP 3] Checking if API server is running...
[OK] Server is running on http://localhost:8000

[STEP 4] Ensuring database schema is up to date...
[OK] Database schema initialized

[STEP 5] Running API integration test...
[OK] API integration test passed

============================================================
All sanity tests passed successfully!
============================================================
```

## Running Individual Tests

If you want to run tests individually:

### Unit tests only:
```bash
python -m pytest tests/ -v
```

### API integration test only:
```bash
python test_api_flow.py
```

## Notes

- The integration test creates a user `testuser@example.com` with password `testpassword123`
- If the user already exists, the test will continue with login
- The test uploads `mock.csv` from the project root
- All expenses are associated with the authenticated user

