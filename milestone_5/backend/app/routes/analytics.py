"""
Analytics, Charts, Insights & Dashboard Overview Routes for Milestone 4.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.database.base import BaseExpenseDatabase
from app.services.insights_service import InsightsService
from app.models.insights import (
    DailySpendingPoint,
    MonthlyTrendPoint,
    InsightCard,
    DashboardOverview
)

router = APIRouter(prefix="/api/analytics", tags=["Smart Insights & Charts"])


def get_insights_service(db: BaseExpenseDatabase = Depends(get_db)) -> InsightsService:
    return InsightsService(db)


@router.get("/dashboard-overview", response_model=DashboardOverview)
def get_dashboard_overview(service: InsightsService = Depends(get_insights_service)):
    """Retrieve full dashboard overview: this month, today, remaining budget, recent transactions, alerts, and insights."""
    return service.get_dashboard_overview()


@router.get("/daily", response_model=List[DailySpendingPoint])
def get_daily_spending(
    month: Optional[str] = Query(default=None, description="Month in YYYY-MM format"),
    service: InsightsService = Depends(get_insights_service)
):
    """Daily spending breakdown for every day of the selected month (Chart C)."""
    return service.get_daily_chart(month=month)


@router.get("/monthly-trend", response_model=List[MonthlyTrendPoint])
def get_monthly_trend(
    limit: int = Query(default=12, ge=1, le=36),
    service: InsightsService = Depends(get_insights_service)
):
    """Monthly spending history trend for line chart (Chart B)."""
    return service.get_monthly_trend_chart(limit=limit)


@router.get("/category-month", response_model=List[Dict[str, Any]])
def get_category_month(
    month: Optional[str] = Query(default=None, description="Month in YYYY-MM format"),
    service: InsightsService = Depends(get_insights_service)
):
    """Category spending breakdown for selected month for doughnut/pie chart (Chart A)."""
    return service.get_category_spending_chart(month=month)


@router.get("/insights", response_model=List[InsightCard])
def get_mom_insights(
    month: Optional[str] = Query(default=None, description="Month in YYYY-MM format"),
    service: InsightsService = Depends(get_insights_service)
):
    """Month-over-month smart financial observations and advice."""
    return service.generate_mom_insights(target_month=month)
