"""
Expense API Endpoints.
Full REST API for expense management, analytics, and health status.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from app.database.base import BaseExpenseDatabase
from app.services.expense_service import ExpenseService
from app.models.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    CategorySummary,
    MonthlySummary,
    TotalSummary
)

router = APIRouter(prefix="/api", tags=["Expenses & Analytics"])


def get_service(db: BaseExpenseDatabase = Depends(get_db)) -> ExpenseService:
    return ExpenseService(db)


# -------------------------------------------------------------
# System & Health Endpoints
# -------------------------------------------------------------

@router.get("/health", response_model=Dict[str, Any])
def health_check(service: ExpenseService = Depends(get_service)):
    """Health check endpoint to test server connectivity and storage status."""
    return service.get_system_status()


@router.get("/status", response_model=Dict[str, Any])
def system_status(service: ExpenseService = Depends(get_service)):
    """Detailed status reporting active mode (LOCAL or CLOUD)."""
    return service.get_system_status()


# -------------------------------------------------------------
# Analytics Endpoints
# -------------------------------------------------------------

@router.get("/analytics/total", response_model=TotalSummary)
def get_total_summary(service: ExpenseService = Depends(get_service)):
    """Retrieve overall expense total, monthly total, and counts."""
    return service.get_total_summary()


@router.get("/analytics/categories", response_model=List[CategorySummary])
def get_category_breakdown(service: ExpenseService = Depends(get_service)):
    """Retrieve category-wise totals with percentages and counts."""
    return service.get_category_breakdown()


@router.get("/analytics/monthly", response_model=List[MonthlySummary])
def get_monthly_breakdown(service: ExpenseService = Depends(get_service)):
    """Retrieve month-by-month spending summaries."""
    return service.get_monthly_breakdown()


# -------------------------------------------------------------
# Expense CRUD Endpoints
# -------------------------------------------------------------

@router.get("/expenses", response_model=List[ExpenseResponse])
def list_expenses(
    limit: Optional[int] = Query(default=None, ge=1, le=1000, description="Max expenses to return"),
    service: ExpenseService = Depends(get_service)
):
    """Retrieve list of recorded expenses, sorted newest first."""
    return service.list_expenses(limit=limit)


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    service: ExpenseService = Depends(get_service)
):
    """Add a new expense with strict validation."""
    return service.add_expense(payload)


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_service)
):
    """Retrieve a single expense by ID."""
    expense = service.get_expense(expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID '{expense_id}' not found."
        )
    return expense


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: str,
    payload: ExpenseUpdate,
    service: ExpenseService = Depends(get_service)
):
    """Update fields of an existing expense."""
    updated = service.update_expense(expense_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID '{expense_id}' not found."
        )
    return updated


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_200_OK)
def delete_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_service)
):
    """Delete an expense by ID."""
    success = service.delete_expense(expense_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID '{expense_id}' not found."
        )
    return {"message": "Expense deleted successfully", "id": expense_id}
