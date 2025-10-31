@echo off
REM Sanity Test Script for Brex Challenge Backend (Windows Batch)
REM This script runs a complete end-to-end test of the API

echo ============================================================
echo Brex Challenge Backend - Sanity Test Suite
echo ============================================================
echo.

REM Step 1: Check if Python is available
echo [STEP 1] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    exit /b 1
)
echo [OK] Python is installed
echo.

REM Step 2: Check if dependencies are installed
echo [STEP 2] Checking dependencies...
python -c "import fastapi, httpx, pytest" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Missing dependencies. Please run: pip install -r requirements.txt
    exit /b 1
)
echo [OK] Dependencies are installed
echo.

REM Step 3: Run unit tests with pytest
echo [STEP 3] Running unit tests...
python -m pytest tests/ -v --tb=short
if errorlevel 1 (
    echo [FAILED] Unit tests failed
    exit /b 1
)
echo [OK] All unit tests passed
echo.

REM Step 4: Check if server is running
echo [STEP 4] Checking if API server is running...
curl -s http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Server is not running on http://localhost:8000
    echo Please start the server with:
    echo   uvicorn app.main:app --reload
    exit /b 1
)
echo [OK] Server is running on http://localhost:8000
echo.

REM Step 5: Initialize database schema (if needed)
echo [STEP 5] Ensuring database schema is up to date...
python -c "from app.database import init_db; init_db()" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Could not initialize database schema
    echo This might be OK if tables already exist
) else (
    echo [OK] Database schema initialized
)
echo.

REM Step 6: Run API integration test
echo [STEP 6] Running API integration test (Create/Login User -^> Upload/Read CSV)...
python test_api_flow.py
if errorlevel 1 (
    echo [FAILED] API integration test failed
    exit /b 1
)
echo [OK] API integration test passed
echo.

REM Summary
echo ============================================================
echo All sanity tests passed successfully!
echo ============================================================
echo.
echo Summary:
echo   - Unit tests: PASSED
echo   - API server: RUNNING
echo   - Database schema: INITIALIZED
echo   - API integration: PASSED
echo.

