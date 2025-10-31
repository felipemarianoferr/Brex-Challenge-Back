from pydantic import BaseModel, EmailStr
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Expense Schemas
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
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CSVUploadResponse(BaseModel):
    message: str
    records_processed: int
    records_inserted: int
    records_updated: int

