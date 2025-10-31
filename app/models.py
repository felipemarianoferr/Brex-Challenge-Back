from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    def __repr__(self):
        return f"<Expense(transaction_id={self.transaction_id}, amount={self.amount}, currency={self.currency})>"

