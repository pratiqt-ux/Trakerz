"""
Pydantic Models for Savings Goals and Contributions in Milestone 4.
"""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, field_validator


class ContributionCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Amount contributed towards the savings goal")
    note: Optional[str] = Field(default="", max_length=255, description="Optional note")
    date: str = Field(..., description="Date of contribution YYYY-MM-DD")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Contribution amount must be greater than zero")
        return round(float(v), 2)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        clean = v.strip()
        try:
            date.fromisoformat(clean)
        except ValueError:
            raise ValueError("Date must be valid ISO format YYYY-MM-DD")
        return clean


class ContributionResponse(BaseModel):
    id: str
    goal_id: str
    amount: float
    note: Optional[str] = ""
    date: str
    created_at: Optional[str] = None


class SavingsGoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Title of goal e.g. New Laptop")
    target_amount: float = Field(..., gt=0, description="Target savings amount in INR")
    deadline: Optional[str] = Field(default=None, description="Optional deadline in YYYY-MM-DD")
    category: Optional[str] = Field(default="General", max_length=50)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Goal title cannot be empty")
        return clean

    @field_validator("target_amount")
    @classmethod
    def validate_target(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Target amount must be greater than zero")
        return round(float(v), 2)

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean = v.strip()
            try:
                date.fromisoformat(clean)
                return clean
            except ValueError:
                raise ValueError("Deadline must be valid ISO format YYYY-MM-DD")
        return None


class SavingsGoalCreate(SavingsGoalBase):
    pass


class SavingsGoalUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    target_amount: Optional[float] = Field(default=None, gt=0)
    deadline: Optional[str] = None
    category: Optional[str] = None
    is_completed: Optional[bool] = None


class SavingsGoalResponse(SavingsGoalBase):
    id: str
    saved_amount: float = 0.0
    remaining_amount: float = 0.0
    progress_percentage: float = 0.0
    is_completed: bool = False
    contributions: List[ContributionResponse] = []
    created_at: Optional[str] = None
