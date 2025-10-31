import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, Numeric, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys
import uuid
from datetime import datetime

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
from app.auth import get_password_hash

# Create test-specific User model compatible with SQLite (String instead of UUID)
class User(TestBase):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())


# Create test-specific Expense model compatible with SQLite (String instead of UUID)
class Expense(TestBase):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(String(50), nullable=False, index=True)
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
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    # Unique constraint: transaction_id must be unique per user
    __table_args__ = (
        UniqueConstraint('user_id', 'transaction_id', name='uq_user_transaction'),
    )

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


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    test_user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    return test_user


@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token for test user"""
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def authenticated_client(client, auth_token):
    """Create an authenticated test client"""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    return client


class TestHelloWorld:
    """Test cases for hello world route"""
    
    def test_hello_world_route(self, client):
        """Test hello world route returns correct message"""
        response = client.get("/hello")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}


class TestAuth:
    """Test cases for authentication endpoints"""
    
    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "password" not in data  # Password should not be in response
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registering with duplicate email fails"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails"""
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails"""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent@example.com", "password": "password123"}
        )
        assert response.status_code == 401


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
    
    def test_upload_csv_without_auth(self, client):
        """Test uploading CSV without authentication fails"""
        with open("mock.csv", "rb") as f:
            files = {"file": ("mock.csv", f, "text/csv")}
            response = client.post("/api/expenses/upload-csv", files=files)
        
        assert response.status_code == 401
    
    def test_upload_csv_with_mock_data(self, authenticated_client):
        """Test uploading CSV file with mock data"""
        # Read mock.csv
        with open("mock.csv", "rb") as f:
            files = {"file": ("mock.csv", f, "text/csv")}
            response = authenticated_client.post("/api/expenses/upload-csv", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "records_processed" in data
        assert "records_inserted" in data
        assert data["records_processed"] > 0
    
    def test_read_default_csv_without_auth(self, client):
        """Test reading default CSV without authentication fails"""
        response = client.post("/api/expenses/read-default-csv")
        assert response.status_code == 401
    
    def test_read_default_csv(self, authenticated_client):
        """Test reading default mock.csv file"""
        response = authenticated_client.post("/api/expenses/read-default-csv")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "records_processed" in data
        assert "records_inserted" in data
        assert data["records_processed"] > 0
    
    def test_list_expenses_without_auth(self, client):
        """Test listing expenses without authentication fails"""
        response = client.get("/api/expenses")
        assert response.status_code == 401
    
    def test_list_expenses(self, authenticated_client):
        """Test listing expenses after importing CSV"""
        # First import the CSV
        authenticated_client.post("/api/expenses/read-default-csv")
        
        # Then list expenses
        response = authenticated_client.get("/api/expenses")
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
        assert "user_id" in expense
    
    def test_get_expense_by_transaction_id(self, authenticated_client):
        """Test getting a specific expense by transaction_id"""
        # First import the CSV
        authenticated_client.post("/api/expenses/read-default-csv")
        
        # Get expense T0001 from mock.csv
        response = authenticated_client.get("/api/expenses/T0001")
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == "T0001"
        assert float(data["amount"]) == 1200.00
        assert data["currency"] == "USD"
        assert data["vendor_name"] == "OpenAI Enterprise"
    
    def test_get_nonexistent_expense(self, authenticated_client):
        """Test getting a non-existent expense returns 404"""
        response = authenticated_client.get("/api/expenses/NONEXISTENT")
        assert response.status_code == 404
    
    def test_get_expense_without_auth(self, client):
        """Test getting expense without authentication fails"""
        response = client.get("/api/expenses/T0001")
        assert response.status_code == 401
    
    def test_upload_invalid_file(self, authenticated_client):
        """Test uploading a non-CSV file"""
        files = {"file": ("test.txt", b"not a csv", "text/plain")}
        response = authenticated_client.post("/api/expenses/upload-csv", files=files)
        assert response.status_code == 400
        assert "CSV file" in response.json()["detail"]
    
    def test_expense_data_from_mock_csv(self, authenticated_client):
        """Test that expense data from mock.csv is correctly parsed and stored"""
        # Import the CSV
        authenticated_client.post("/api/expenses/read-default-csv")
        
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
            response = authenticated_client.get(f"/api/expenses/{test_case['transaction_id']}")
            assert response.status_code == 200
            data = response.json()
            assert data["transaction_id"] == test_case["transaction_id"]
            assert float(data["amount"]) == test_case["amount"]
            assert data["vendor_name"] == test_case["vendor_name"]
            assert data["department"] == test_case["department"]
            assert data["expense_type"] == test_case["expense_type"]
    
    def test_expense_pagination(self, authenticated_client):
        """Test pagination in list expenses endpoint"""
        # Import the CSV
        authenticated_client.post("/api/expenses/read-default-csv")
        
        # Get first page
        response = authenticated_client.get("/api/expenses?skip=0&limit=5")
        assert response.status_code == 200
        first_page = response.json()
        assert len(first_page) <= 5
        
        # Get second page
        response = authenticated_client.get("/api/expenses?skip=5&limit=5")
        assert response.status_code == 200
        second_page = response.json()
        
        # Verify different results
        if len(first_page) > 0 and len(second_page) > 0:
            assert first_page[0]["transaction_id"] != second_page[0]["transaction_id"]
    
    def test_user_isolation(self, client, db_session):
        """Test that users can only see their own expenses"""
        # Create two users
        user1 = User(
            email="user1@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        user2 = User(
            email="user2@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        # Get tokens for both users
        response1 = client.post(
            "/api/auth/login",
            data={"username": "user1@example.com", "password": "password123"}
        )
        token1 = response1.json()["access_token"]
        
        response2 = client.post(
            "/api/auth/login",
            data={"username": "user2@example.com", "password": "password123"}
        )
        token2 = response2.json()["access_token"]
        
        # User1 imports CSV
        client.headers = {"Authorization": f"Bearer {token1}"}
        client.post("/api/expenses/read-default-csv")
        
        # User1 should see expenses
        response = client.get("/api/expenses")
        assert response.status_code == 200
        assert len(response.json()) > 0
        
        # User2 should see no expenses
        client.headers = {"Authorization": f"Bearer {token2}"}
        response = client.get("/api/expenses")
        assert response.status_code == 200
        assert len(response.json()) == 0
