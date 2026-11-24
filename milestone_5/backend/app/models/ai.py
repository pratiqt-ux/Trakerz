"""
Pydantic Models for Milestone 5 AI Financial Intelligence Features:
- Smart Categorization
- Unusual Spending Anomaly Detection
- Monthly Spending Forecast
- AI Financial Chat Assistant
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# -------------------------------------------------------------
# 1. Smart Categorization
# -------------------------------------------------------------
class CategorizeRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: Optional[float] = Field(default=None)

    @field_validator("description")
    @classmethod
    def clean_desc(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Description cannot be empty")
        return clean


class CategorizeResponse(BaseModel):
    suggested_category: str
    suggested_description: str
    confidence: str  # "high", "medium", "low"
    source: str      # "rule_based", "ai"
    reason: str


# -------------------------------------------------------------
# 2. Unusual Spending Detection
# -------------------------------------------------------------
class SpendingAnomaly(BaseModel):
    id: str
    anomaly_type: str  # "daily_category_spike", "weekly_category_surge", "large_transaction"
    severity: str      # "info", "warning"
    category: Optional[str] = None
    title: str
    message: str
    explanation: str
    ratio: Optional[float] = None


# -------------------------------------------------------------
# 3. Monthly Spending Forecast
# -------------------------------------------------------------
class ForecastPoint(BaseModel):
    day: int
    date: str
    actual_cumulative: Optional[float] = None
    projected_cumulative: float


class MonthlyForecast(BaseModel):
    month: str
    current_spending: float
    days_elapsed: int
    total_days_in_month: int
    remaining_days: int
    average_daily_spending: float
    estimated_month_end_spending: float
    previous_month_spending: float
    previous_month_diff_pct: Optional[float] = None
    confidence_level: str  # "insufficient_data", "low", "moderate", "high"
    is_estimate: bool = True
    note: str
    projected_series: List[ForecastPoint] = []


# -------------------------------------------------------------
# 4. AI Financial Chat Assistant
# -------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Chat message cannot be empty")
        return clean


class ChatResponse(BaseModel):
    reply: str
    ai_available: bool
    provider: str
    model: Optional[str] = None
    error_type: Optional[str] = None  # "not_configured", "invalid_key", "rate_limit", "network_error", "timeout", "api_error"
    data_context_used: Optional[Dict[str, Any]] = None


class AIStatusResponse(BaseModel):
    ai_configured: bool
    provider: str
    model: str
    message: str
