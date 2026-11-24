"""
Savings Goals & Contributions API Routes for Milestone 4.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.database.base import BaseExpenseDatabase
from app.services.savings_service import SavingsService
from app.models.savings import (
    SavingsGoalCreate,
    SavingsGoalUpdate,
    SavingsGoalResponse,
    ContributionCreate,
    ContributionResponse
)

router = APIRouter(prefix="/api/savings-goals", tags=["Savings Goals"])


def get_savings_service(db: BaseExpenseDatabase = Depends(get_db)) -> SavingsService:
    return SavingsService(db)


@router.get("", response_model=List[SavingsGoalResponse])
def list_goals(service: SavingsService = Depends(get_savings_service)):
    """Retrieve all savings goals with progress and contributions."""
    return service.list_goals()


@router.post("", response_model=SavingsGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: SavingsGoalCreate,
    service: SavingsService = Depends(get_savings_service)
):
    """Create a new savings goal."""
    return service.create_goal(payload)


@router.get("/{goal_id}", response_model=SavingsGoalResponse)
def get_goal(
    goal_id: str,
    service: SavingsService = Depends(get_savings_service)
):
    """Retrieve a single savings goal with detailed contribution history."""
    goal = service.get_goal(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Savings goal with ID '{goal_id}' not found."
        )
    return goal


@router.put("/{goal_id}", response_model=SavingsGoalResponse)
def update_goal(
    goal_id: str,
    payload: SavingsGoalUpdate,
    service: SavingsService = Depends(get_savings_service)
):
    """Update goal title, target amount, deadline, or completion status."""
    updated = service.update_goal(goal_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Savings goal with ID '{goal_id}' not found."
        )
    return updated


@router.delete("/{goal_id}", status_code=status.HTTP_200_OK)
def delete_goal(
    goal_id: str,
    service: SavingsService = Depends(get_savings_service)
):
    """Delete a savings goal."""
    success = service.delete_goal(goal_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Savings goal with ID '{goal_id}' not found."
        )
    return {"message": "Savings goal deleted successfully", "id": goal_id}


@router.post("/{goal_id}/contribute", response_model=ContributionResponse, status_code=status.HTTP_201_CREATED)
def add_contribution(
    goal_id: str,
    payload: ContributionCreate,
    service: SavingsService = Depends(get_savings_service)
):
    """Add a deposit/contribution to a savings goal."""
    try:
        return service.add_contribution(goal_id, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/contributions/{contrib_id}", status_code=status.HTTP_200_OK)
def delete_contribution(
    contrib_id: str,
    service: SavingsService = Depends(get_savings_service)
):
    """Remove a contribution from a goal."""
    success = service.delete_contribution(contrib_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contribution with ID '{contrib_id}' not found."
        )
    return {"message": "Contribution deleted successfully", "id": contrib_id}
