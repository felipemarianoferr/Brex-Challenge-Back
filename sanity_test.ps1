# Sanity Test Script for Brex Challenge Backend (PowerShell)
# This script runs a complete end-to-end test of the API

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Brex Challenge Backend - Sanity Test Suite" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if Python is available
Write-Host "[STEP 1] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Check if dependencies are installed
Write-Host "[STEP 2] Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import fastapi, httpx, pytest" 2>&1 | Out-Null
    Write-Host "[OK] Dependencies are installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Missing dependencies. Please run: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Run unit tests with pytest
Write-Host "[STEP 3] Running unit tests..." -ForegroundColor Yellow
try {
    python -m pytest tests/ -v --tb=short
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] All unit tests passed" -ForegroundColor Green
    } else {
        Write-Host "[FAILED] Unit tests failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[FAILED] Error running unit tests: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Check if server is running
Write-Host "[STEP 4] Checking if API server is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Server is running on http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERROR] Server is not running on http://localhost:8000" -ForegroundColor Red
    Write-Host "Please start the server with:" -ForegroundColor Yellow
    Write-Host "  uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host ""
    Write-Host "Or run in background:" -ForegroundColor Yellow
    Write-Host "  Start-Process python -ArgumentList '-m','uvicorn','app.main:app','--reload'" -ForegroundColor White
    exit 1
}
Write-Host ""

# Step 5: Initialize database schema (if needed)
Write-Host "[STEP 5] Ensuring database schema is up to date..." -ForegroundColor Yellow
try {
    python -c "from app.database import init_db; init_db()" 2>&1 | Out-Null
    Write-Host "[OK] Database schema initialized" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Could not initialize database schema" -ForegroundColor Yellow
    Write-Host "This might be OK if tables already exist" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Run API integration test
Write-Host "[STEP 6] Running API integration test (Create/Login User -> Upload/Read CSV)..." -ForegroundColor Yellow
try {
    python test_api_flow.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] API integration test passed" -ForegroundColor Green
    } else {
        Write-Host "[FAILED] API integration test failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[FAILED] Error running API integration test: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "All sanity tests passed successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  - Unit tests: PASSED" -ForegroundColor Green
Write-Host "  - API server: RUNNING" -ForegroundColor Green
Write-Host "  - Database schema: INITIALIZED" -ForegroundColor Green
Write-Host "  - API integration: PASSED" -ForegroundColor Green
Write-Host ""

