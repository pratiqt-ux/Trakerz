"""
AI & Financial Intelligence Routes for Milestone 5:
- AI Financial Chat Assistant (/api/ai/chat, /api/ai/status)
- Smart Expense Categorization (/api/ai/categorize)
- Unusual Spending Detection (/api/analytics/anomalies)
- Monthly Spending Forecast (/api/analytics/forecast)
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.database.base import BaseExpenseDatabase
from app.models.ai import (
    CategorizeRequest,
    CategorizeResponse,
    SpendingAnomaly,
    MonthlyForecast,
    ChatRequest,
    ChatResponse,
    AIStatusResponse
)
from app.services.categorization_service import CategorizationService
from app.services.anomaly_service import AnomalyDetectionService
from app.services.forecast_service import ForecastService
from app.services.ai_chat_service import AIChatService

router = APIRouter(tags=["Milestone 5: AI & Financial Intelligence"])


def get_cat_service(db: BaseExpenseDatabase = Depends(get_db)) -> CategorizationService:
    return CategorizationService(db)


def get_anomaly_service(db: BaseExpenseDatabase = Depends(get_db)) -> AnomalyDetectionService:
    return AnomalyDetectionService(db)


def get_forecast_service(db: BaseExpenseDatabase = Depends(get_db)) -> ForecastService:
    return ForecastService(db)


def get_chat_service(db: BaseExpenseDatabase = Depends(get_db)) -> AIChatService:
    return AIChatService(db)


@router.get("/api/ai/status", response_model=AIStatusResponse)
def ai_status(service: AIChatService = Depends(get_chat_service)):
    """Check whether the AI Chat Assistant API key is configured."""
    return service.get_status()


@router.post("/api/ai/chat", response_model=ChatResponse)
async def ai_chat(
    payload: ChatRequest,
    service: AIChatService = Depends(get_chat_service)
):
    """Converse with Trakerz AI Assistant grounded in the user's real financial data."""
    return await service.chat(payload)


@router.post("/api/ai/categorize", response_model=CategorizeResponse)
async def smart_categorize(
    payload: CategorizeRequest,
    service: CategorizationService = Depends(get_cat_service)
):
    """Suggest category and cleaned description for a transaction description."""
    return await service.suggest_category(payload.description, payload.amount)


@router.get("/api/analytics/anomalies", response_model=List[SpendingAnomaly])
def get_spending_anomalies(
    service: AnomalyDetectionService = Depends(get_anomaly_service)
):
    """Detect unusual spending spikes and large transactions from historical data."""
    return service.detect_anomalies()


@router.get("/api/analytics/forecast", response_model=MonthlyForecast)
def get_monthly_forecast(
    month: Optional[str] = Query(default=None, description="Month in YYYY-MM format"),
    service: ForecastService = Depends(get_forecast_service)
):
    """Estimate month-end spending based on current pace and historical data."""
    return service.compute_monthly_forecast(target_month=month)
