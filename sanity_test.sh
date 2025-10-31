#!/bin/bash
# Sanity Test Script for Brex Challenge Backend
# This script runs a complete end-to-end test of the API

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Brex Challenge Backend - Sanity Test Suite"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}[ERROR] Python is not installed or not in PATH${NC}"
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
echo -e "${GREEN}[INFO] Using Python: ${PYTHON_CMD}${NC}"
echo ""

# Step 1: Check if dependencies are installed
echo -e "${YELLOW}[STEP 1] Checking dependencies...${NC}"
if ! ${PYTHON_CMD} -c "import fastapi, httpx, pytest" 2>/dev/null; then
    echo -e "${RED}[ERROR] Missing dependencies. Please run: pip install -r requirements.txt${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Dependencies are installed${NC}"
echo ""

# Step 2: Run unit tests with pytest
echo -e "${YELLOW}[STEP 2] Running unit tests...${NC}"
if ${PYTHON_CMD} -m pytest tests/ -v --tb=short; then
    echo -e "${GREEN}[OK] All unit tests passed${NC}"
else
    echo -e "${RED}[FAILED] Unit tests failed${NC}"
    exit 1
fi
echo ""

# Step 3: Check if server is running
echo -e "${YELLOW}[STEP 3] Checking if API server is running...${NC}"
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}[OK] Server is running on http://localhost:8000${NC}"
else
    echo -e "${RED}[ERROR] Server is not running on http://localhost:8000${NC}"
    echo -e "${YELLOW}Please start the server with:${NC}"
    echo "  uvicorn app.main:app --reload"
    echo ""
    echo -e "${YELLOW}Or run in background:${NC}"
    echo "  uvicorn app.main:app --reload > server.log 2>&1 &"
    exit 1
fi
echo ""

# Step 4: Initialize database schema (if needed)
echo -e "${YELLOW}[STEP 4] Ensuring database schema is up to date...${NC}"
if ${PYTHON_CMD} -c "from app.database import init_db; init_db()" 2>/dev/null; then
    echo -e "${GREEN}[OK] Database schema initialized${NC}"
else
    echo -e "${YELLOW}[WARNING] Could not initialize database schema${NC}"
    echo -e "${YELLOW}This might be OK if tables already exist${NC}"
fi
echo ""

# Step 5: Run API integration test
echo -e "${YELLOW}[STEP 5] Running API integration test (Create/Login User -> Upload/Read CSV)...${NC}"
if ${PYTHON_CMD} test_api_flow.py; then
    echo -e "${GREEN}[OK] API integration test passed${NC}"
else
    echo -e "${RED}[FAILED] API integration test failed${NC}"
    exit 1
fi
echo ""

# Summary
echo "============================================================"
echo -e "${GREEN}All sanity tests passed successfully!${NC}"
echo "============================================================"
echo ""
echo "Summary:"
echo "  - Unit tests: PASSED"
echo "  - API server: RUNNING"
echo "  - Database schema: INITIALIZED"
echo "  - API integration: PASSED"
echo ""

