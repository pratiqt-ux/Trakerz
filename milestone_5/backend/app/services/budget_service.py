"""
Budget Service Layer for Milestone 4.
Handles budget creation, calculation of spent/remaining amounts,
and generation of 80% and 100% spending alert warnings.
"""
from typing import List, Optional
from datetime import datetime
from app.database.base import BaseExpenseDatabase
from app.models.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetAlert
)


class BudgetService:
    def __init__(self, db: BaseExpenseDatabase):
        self.db = db

    def set_budget(self, data: BudgetCreate) -> BudgetResponse:
        created = self.db.upsert_budget(data.model_dump())
        return BudgetResponse(**created)

    def list_budgets(self, month: Optional[str] = None) -> List[BudgetResponse]:
        if not month:
            month = datetime.now().strftime("%Y-%m")
        rows = self.db.get_budgets(month=month)
        return [BudgetResponse(**r) for r in rows]

    def get_budget(self, budget_id: str) -> Optional[BudgetResponse]:
        item = self.db.get_budget_by_id(budget_id)
        if not item:
            return None
        return BudgetResponse(**item)

    def update_budget(self, budget_id: str, data: BudgetUpdate) -> Optional[BudgetResponse]:
        current = self.get_budget(budget_id)
        if not current:
            return None
        payload = {
            "category": current.category,
            "month": current.month,
            "amount": data.amount if data.amount is not None else current.amount
        }
        updated = self.db.upsert_budget(payload)
        return BudgetResponse(**updated)

    def delete_budget(self, budget_id: str) -> bool:
        return self.db.delete_budget(budget_id)

    def get_budget_alerts(self, month: Optional[str] = None) -> List[BudgetAlert]:
        budgets = self.list_budgets(month=month)
        alerts: List[BudgetAlert] = []

        for b in budgets:
            if b.status == "exceeded":
                alerts.append(BudgetAlert(
                    category=b.category,
                    budget_amount=b.amount,
                    spent_amount=b.spent_amount,
                    percentage_used=b.percentage_used,
                    alert_type="exceeded",
                    message=f"Budget exceeded! You spent ₹{b.spent_amount:,.2f} on {b.category} (₹{b.overspent_amount:,.2f} over your ₹{b.amount:,.2f} limit)."
                ))
            elif b.status == "warning":
                alerts.append(BudgetAlert(
                    category=b.category,
                    budget_amount=b.amount,
                    spent_amount=b.spent_amount,
                    percentage_used=b.percentage_used,
                    alert_type="warning",
                    message=f"Warning: {b.category} spending is at {b.percentage_used}% (₹{b.spent_amount:,.2f} of ₹{b.amount:,.2f}). Only ₹{b.remaining_amount:,.2f} remaining."
                ))

        return alerts
