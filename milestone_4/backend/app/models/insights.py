"""
Pydantic Models for Financial Insights and Chart Data in Milestone 4.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class DailySpendingPoint(BaseModel):
    date: str  # YYYY-MM-DD
    day: int
    day_name: str  # Mon, Tue, etc.
    amount: float
    transaction_count: int


class MonthlyTrendPoint(BaseModel):
    month: str  # YYYY-MM
    display_name: str  # e.g. "Nov 2026"
    amount: float
    transaction_count: int


class InsightCard(BaseModel):
    id: str
    type: str  # "increase", "decrease", "highlight", "budget", "info"
    severity: str  # "info", "warning", "success", "alert"
    title: str
    description: str
    metric: Optional[str] = None


class DashboardOverview(BaseModel):
    this_month_spending: float
    today_spending: float
    total_budget_amount: float
    remaining_monthly_budget: float
    budget_usage_percentage: float
    transaction_count: int
    recent_transactions: List[Dict[str, Any]]
    active_alerts: List[Dict[str, Any]]
    top_insights: List[InsightCard]
