from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


class ExpenseBase(BaseModel):
    transaction_id: str
    amount: Decimal
    currency: str
    datetime: datetime
    payment_method: Optional[str] = None
    src_account: Optional[str] = None
    dst_account: Optional[str] = None
    vendor_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    recurrency: Optional[str] = None
    department: Optional[str] = None
    expense_type: Optional[str] = None
    expense_name: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    id: UUID

    class Config:
        from_attributes = True


class CSVUploadResponse(BaseModel):
    message: str
    records_processed: int
    records_inserted: int
    records_updated: int

