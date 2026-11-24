"""
Pydantic Models for Category Budgets & Alerts in Milestone 4.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class BudgetBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=50, description="Expense category e.g. Food, Travel")
    month: str = Field(..., description="Month in YYYY-MM format")
    amount: float = Field(..., gt=0, description="Monthly allocated budget in INR")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Category cannot be empty")
        return clean

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: str) -> str:
        clean = v.strip()
        parts = clean.split("-")
        if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
            raise ValueError("Month must be in YYYY-MM format")
        try:
            m = int(parts[1])
            if not (1 <= m <= 12):
                raise ValueError("Month must be between 01 and 12")
        except ValueError:
            raise ValueError("Month must be numeric in YYYY-MM format")
        return clean

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Budget amount must be greater than zero")
        return round(float(v), 2)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v <= 0:
                raise ValueError("Amount must be greater than zero")
            return round(float(v), 2)
        return v


class BudgetResponse(BudgetBase):
    id: str
    spent_amount: float = 0.0
    remaining_amount: float = 0.0
    percentage_used: float = 0.0
    status: str = "normal"  # "normal", "warning" (>=80%), "exceeded" (>=100%)
    overspent_amount: float = 0.0
    created_at: Optional[str] = None


class BudgetAlert(BaseModel):
    category: str
    budget_amount: float
    spent_amount: float
    percentage_used: float
    alert_type: str  # "warning" (80%), "exceeded" (100%)
    message: str
