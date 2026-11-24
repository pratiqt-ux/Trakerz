"""
Budget API Routes for Milestone 4.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from app.database.base import BaseExpenseDatabase
from app.services.budget_service import BudgetService
from app.models.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetAlert
)

router = APIRouter(prefix="/api/budgets", tags=["Budgets & Alerts"])


def get_budget_service(db: BaseExpenseDatabase = Depends(get_db)) -> BudgetService:
    return BudgetService(db)


@router.get("", response_model=List[BudgetResponse])
def get_budgets(
    month: Optional[str] = Query(default=None, description="Month in YYYY-MM format"),
    service: BudgetService = Depends(get_budget_service)
):
    """Retrieve all category budgets for a specific month (defaults to current month)."""
    return service.list_budgets(month=month)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def set_budget(
    payload: BudgetCreate,
    service: BudgetService = Depends(get_budget_service)
):
    """Set or update category budget for a month."""
    return service.set_budget(payload)


@router.get("/alerts", response_model=List[BudgetAlert])
def get_budget_alerts(
    month: Optional[str] = Query(default=None, description="Month in YYYY-MM format"),
    service: BudgetService = Depends(get_budget_service)
):
    """Get active budget warnings (>=80%) and exceeded alerts (>=100%)."""
    return service.get_budget_alerts(month=month)


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: str,
    service: BudgetService = Depends(get_budget_service)
):
    """Retrieve single budget by ID."""
    b = service.get_budget(budget_id)
    if not b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID '{budget_id}' not found."
        )
    return b


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: str,
    payload: BudgetUpdate,
    service: BudgetService = Depends(get_budget_service)
):
    """Update allocated budget amount."""
    updated = service.update_budget(budget_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID '{budget_id}' not found."
        )
    return updated


@router.delete("/{budget_id}", status_code=status.HTTP_200_OK)
def delete_budget(
    budget_id: str,
    service: BudgetService = Depends(get_budget_service)
):
    """Delete a budget by ID."""
    success = service.delete_budget(budget_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with ID '{budget_id}' not found."
        )
    return {"message": "Budget deleted successfully", "id": budget_id}
