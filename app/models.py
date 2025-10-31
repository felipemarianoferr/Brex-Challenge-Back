from sqlalchemy import Column, String, Numeric, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime as dt
import uuid
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=dt.utcnow)

    # Relationship to expenses
    expenses = relationship("Expense", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(email={self.email}, id={self.id})>"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
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
    created_at = Column(DateTime, nullable=False, default=dt.utcnow)

    # Relationship to user
    owner = relationship("User", back_populates="expenses")
    
    # Unique constraint: transaction_id must be unique per user
    __table_args__ = (
        UniqueConstraint('user_id', 'transaction_id', name='uq_user_transaction'),
    )

    def __repr__(self):
        return f"<Expense(transaction_id={self.transaction_id}, amount={self.amount}, currency={self.currency})>"

