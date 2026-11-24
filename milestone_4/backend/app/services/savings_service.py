"""
Savings Goals & Contribution Service Layer for Milestone 4.
"""
from typing import List, Optional
from app.database.base import BaseExpenseDatabase
from app.models.savings import (
    SavingsGoalCreate,
    SavingsGoalUpdate,
    SavingsGoalResponse,
    ContributionCreate,
    ContributionResponse
)


class SavingsService:
    def __init__(self, db: BaseExpenseDatabase):
        self.db = db

    def create_goal(self, data: SavingsGoalCreate) -> SavingsGoalResponse:
        goal = self.db.create_savings_goal(data.model_dump())
        return SavingsGoalResponse(**goal)

    def list_goals(self) -> List[SavingsGoalResponse]:
        rows = self.db.get_savings_goals()
        return [SavingsGoalResponse(**r) for r in rows]

    def get_goal(self, goal_id: str) -> Optional[SavingsGoalResponse]:
        item = self.db.get_savings_goal(goal_id)
        if not item:
            return None
        return SavingsGoalResponse(**item)

    def update_goal(self, goal_id: str, data: SavingsGoalUpdate) -> Optional[SavingsGoalResponse]:
        payload = {k: v for k, v in data.model_dump().items() if v is not None}
        updated = self.db.update_savings_goal(goal_id, payload)
        if not updated:
            return None
        return SavingsGoalResponse(**updated)

    def delete_goal(self, goal_id: str) -> bool:
        return self.db.delete_savings_goal(goal_id)

    def add_contribution(self, goal_id: str, data: ContributionCreate) -> ContributionResponse:
        # Check if goal exists
        goal = self.db.get_savings_goal(goal_id)
        if not goal:
            raise ValueError(f"Savings goal with ID {goal_id} not found")

        contrib = self.db.add_savings_contribution(goal_id, data.model_dump())
        return ContributionResponse(**contrib)

    def delete_contribution(self, contrib_id: str) -> bool:
        return self.db.delete_savings_contribution(contrib_id)
