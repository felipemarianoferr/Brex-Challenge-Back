import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Override database engine BEFORE importing app to prevent PostgreSQL connection
import app.database

# Create test-specific Base for SQLite compatibility
TestBase = declarative_base()

# Create test database in memory (SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Override the database engine in app.database before importing app.main
# This prevents the startup event from trying to connect to PostgreSQL
app.database.engine = test_engine
app.database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

from app.main import app as fastapi_app
from app.database import get_db, init_db

# Create test-specific Expense model compatible with SQLite (String instead of UUID)
class Expense(TestBase):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    datetime = Column(DateTime, nullable=False)
    payment_method = Column(String(50), nullable=True)
    src_account = Column(String(100), nullable=True)
    dst_account = Column(String(100), nullable=True)
    vendor_name = Column(String(200), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    recurrency = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    expense_type = Column(String(100), nullable=True)
    expense_name = Column(String(500), nullable=True)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session():
    """Create a test database session"""
    TestBase.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        TestBase.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override database dependency
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    # Override init_db to use test database instead of PostgreSQL
    def mock_init_db():
        TestBase.metadata.create_all(bind=test_engine)
    
    # Temporarily replace init_db
    import app.database
    original_init_db = app.database.init_db
    app.database.init_db = mock_init_db
    
    with TestClient(fastapi_app) as test_client:
        yield test_client
    
    # Restore original functions
    fastapi_app.dependency_overrides.clear()
    import app.database
    app.database.init_db = original_init_db


class TestHelloWorld:
    """Test cases for hello world route"""
    
    def test_hello_world_route(self, client):
        """Test hello world route returns correct message"""
        response = client.get("/hello")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}


class TestExpensesAPI:
    """Test cases for expenses API using mock.csv data"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_upload_csv_with_mock_data(self, client):
        """Test uploading CSV file with mock data"""
        # Read mock.csv
        with open("mock.csv", "rb") as f:
            files = {"file": ("mock.csv", f, "text/csv")}
            response = client.post("/api/expenses/upload-csv", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "records_processed" in data
        assert "records_inserted" in data
        assert data["records_processed"] > 0
    
    def test_read_default_csv(self, client):
        """Test reading default mock.csv file"""
        response = client.post("/api/expenses/read-default-csv")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "records_processed" in data
        assert "records_inserted" in data
        assert data["records_processed"] > 0
    
    def test_list_expenses(self, client):
        """Test listing expenses after importing CSV"""
        # First import the CSV
        client.post("/api/expenses/read-default-csv")
        
        # Then list expenses
        response = client.get("/api/expenses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check expense structure
        expense = data[0]
        assert "transaction_id" in expense
        assert "amount" in expense
        assert "currency" in expense
        assert "datetime" in expense
    
    def test_get_expense_by_transaction_id(self, client):
        """Test getting a specific expense by transaction_id"""
        # First import the CSV
        client.post("/api/expenses/read-default-csv")
        
        # Get expense T0001 from mock.csv
        response = client.get("/api/expenses/T0001")
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == "T0001"
        assert float(data["amount"]) == 1200.00
        assert data["currency"] == "USD"
        assert data["vendor_name"] == "OpenAI Enterprise"
    
    def test_get_nonexistent_expense(self, client):
        """Test getting a non-existent expense returns 404"""
        response = client.get("/api/expenses/NONEXISTENT")
        assert response.status_code == 404
    
    def test_upload_invalid_file(self, client):
        """Test uploading a non-CSV file"""
        files = {"file": ("test.txt", b"not a csv", "text/plain")}
        response = client.post("/api/expenses/upload-csv", files=files)
        assert response.status_code == 400
        assert "CSV file" in response.json()["detail"]
    
    def test_expense_data_from_mock_csv(self, client):
        """Test that expense data from mock.csv is correctly parsed and stored"""
        # Import the CSV
        client.post("/api/expenses/read-default-csv")
        
        # Verify specific transactions from mock.csv
        test_cases = [
            {
                "transaction_id": "T0001",
                "amount": 1200.00,
                "vendor_name": "OpenAI Enterprise",
                "department": "Engineering",
                "expense_type": "subscriptions"
            },
            {
                "transaction_id": "T0002",
                "amount": 8000.00,
                "vendor_name": "City Offices Ltd",
                "department": "Operations",
                "expense_type": "rent"
            },
            {
                "transaction_id": "T0003",
                "amount": 3200.00,
                "vendor_name": "Amazon Web Services",
                "department": "Engineering",
                "expense_type": "infrastructure"
            }
        ]
        
        for test_case in test_cases:
            response = client.get(f"/api/expenses/{test_case['transaction_id']}")
            assert response.status_code == 200
            data = response.json()
            assert data["transaction_id"] == test_case["transaction_id"]
            assert float(data["amount"]) == test_case["amount"]
            assert data["vendor_name"] == test_case["vendor_name"]
            assert data["department"] == test_case["department"]
            assert data["expense_type"] == test_case["expense_type"]
    
    def test_expense_pagination(self, client):
        """Test pagination in list expenses endpoint"""
        # Import the CSV
        client.post("/api/expenses/read-default-csv")
        
        # Get first page
        response = client.get("/api/expenses?skip=0&limit=5")
        assert response.status_code == 200
        first_page = response.json()
        assert len(first_page) <= 5
        
        # Get second page
        response = client.get("/api/expenses?skip=5&limit=5")
        assert response.status_code == 200
        second_page = response.json()
        
        # Verify different results
        if len(first_page) > 0 and len(second_page) > 0:
            assert first_page[0]["transaction_id"] != second_page[0]["transaction_id"]

