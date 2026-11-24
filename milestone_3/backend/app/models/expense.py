"""
Pydantic Models for Expense Data Validation & API Serialization.
"""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, field_validator


class ExpenseBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=50, description="Expense category e.g. Food, Travel")
    amount: float = Field(..., gt=0, description="Expense amount in INR (must be > 0)")
    description: Optional[str] = Field(default="", max_length=255, description="Optional brief description")
    date: str = Field(..., description="Date of expense in YYYY-MM-DD format")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Category cannot be empty or only whitespace")
        return clean

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(float(v), 2)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        clean = v.strip()
        try:
            # Verify valid ISO date format YYYY-MM-DD
            date.fromisoformat(clean)
        except ValueError:
            raise ValueError("Date must be in valid YYYY-MM-DD format")
        return clean

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: Optional[str]) -> str:
        return (v or "").strip()


class ExpenseCreate(ExpenseBase):
    """Payload for creating a new expense."""
    pass


class ExpenseUpdate(BaseModel):
    """Payload for updating an existing expense."""
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    amount: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, max_length=255)
    date: Optional[str] = Field(default=None)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                raise ValueError("Category cannot be empty")
            return clean
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("Amount must be greater than zero")
            return round(float(v), 2)
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                date.fromisoformat(v.strip())
            except ValueError:
                raise ValueError("Date must be in valid YYYY-MM-DD format")
            return v.strip()
        return v


class ExpenseResponse(ExpenseBase):
    """Model returned to API clients."""
    id: str = Field(..., description="Unique ID of the expense (string for SQLite/Firestore compatibility)")
    created_at: Optional[str] = Field(default=None, description="ISO timestamp when created")

    class Config:
        from_attributes = True


class CategorySummary(BaseModel):
    category: str
    total: float
    percentage: float
    count: int


class MonthlySummary(BaseModel):
    month: str  # YYYY-MM
    total: float
    count: int
    is_current_month: bool


class TotalSummary(BaseModel):
    total_amount: float
    expense_count: int
    current_month_total: float
    storage_mode: str
    database_type: str
