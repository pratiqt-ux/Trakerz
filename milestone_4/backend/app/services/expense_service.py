"""
Expense Service Layer.
Encapsulates business logic, data formatting, and metrics calculation.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database.base import BaseExpenseDatabase
from app.models.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    CategorySummary,
    MonthlySummary,
    TotalSummary
)


class ExpenseService:
    def __init__(self, db: BaseExpenseDatabase):
        self.db = db

    def add_expense(self, data: ExpenseCreate) -> ExpenseResponse:
        created = self.db.create_expense(data.model_dump())
        return ExpenseResponse(**created)

    def list_expenses(self, limit: Optional[int] = None) -> List[ExpenseResponse]:
        rows = self.db.get_expenses(limit=limit)
        return [ExpenseResponse(**r) for r in rows]

    def get_expense(self, expense_id: str) -> Optional[ExpenseResponse]:
        item = self.db.get_expense(expense_id)
        if not item:
            return None
        return ExpenseResponse(**item)

    def update_expense(self, expense_id: str, data: ExpenseUpdate) -> Optional[ExpenseResponse]:
        # Filter out None values from the update payload
        payload = {k: v for k, v in data.model_dump().items() if v is not None}
        if not payload:
            # Nothing to update, return current
            return self.get_expense(expense_id)

        updated = self.db.update_expense(expense_id, payload)
        if not updated:
            return None
        return ExpenseResponse(**updated)

    def delete_expense(self, expense_id: str) -> bool:
        return self.db.delete_expense(expense_id)

    def get_total_summary(self) -> TotalSummary:
        total = self.db.get_total_expense()
        expenses = self.db.get_expenses()
        current_ym = datetime.now().strftime("%Y-%m")
        cur_month_total = sum(
            float(e.get("amount", 0.0))
            for e in expenses
            if str(e.get("date", "")).startswith(current_ym)
        )
        info = self.db.get_backend_info()

        return TotalSummary(
            total_amount=round(total, 2),
            expense_count=len(expenses),
            current_month_total=round(cur_month_total, 2),
            storage_mode=info.get("mode", "local"),
            database_type=info.get("database_type", "sqlite")
        )

    def get_category_breakdown(self) -> List[CategorySummary]:
        rows = self.db.get_category_totals()
        return [CategorySummary(**r) for r in rows]

    def get_monthly_breakdown(self) -> List[MonthlySummary]:
        rows = self.db.get_monthly_totals()
        return [MonthlySummary(**r) for r in rows]

    def get_system_status(self) -> Dict[str, Any]:
        info = self.db.get_backend_info()
        expenses = self.db.get_expenses()
        return {
            "status": "healthy",
            "backend": "FastAPI",
            "version": "3.0.0",
            "mode": info.get("mode", "local"),
            "database": info.get("database_type", "sqlite"),
            "cloud_configured": info.get("cloud_configured", False),
            "total_expenses_recorded": len(expenses),
            "timestamp": datetime.now().isoformat()
        }
