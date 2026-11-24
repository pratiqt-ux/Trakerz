"""
Base Database Interface for Trakerz Milestone 4.
Defines abstract contracts for expenses, budgets, savings goals, and analytics.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseExpenseDatabase(ABC):
    """Abstract interface for Trakerz storage engines."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize database connection, schema or collections."""
        pass

    # ----------------- Expenses -----------------
    @abstractmethod
    def create_expense(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_expenses(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_expense(self, expense_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_expense(self, expense_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_expense(self, expense_id: str) -> bool:
        pass

    @abstractmethod
    def get_total_expense(self) -> float:
        pass

    @abstractmethod
    def get_category_totals(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_monthly_totals(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_backend_info(self) -> Dict[str, Any]:
        pass

    # ----------------- Budgets -----------------
    @abstractmethod
    def upsert_budget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update budget for a category and month."""
        pass

    @abstractmethod
    def get_budgets(self, month: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve category budgets."""
        pass

    @abstractmethod
    def get_budget_by_id(self, budget_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single budget by ID."""
        pass

    @abstractmethod
    def delete_budget(self, budget_id: str) -> bool:
        """Delete budget by ID."""
        pass

    # ----------------- Savings Goals -----------------
    @abstractmethod
    def create_savings_goal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_savings_goals(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_savings_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_savings_goal(self, goal_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_savings_goal(self, goal_id: str) -> bool:
        pass

    @abstractmethod
    def add_savings_contribution(self, goal_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_contributions_for_goal(self, goal_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_savings_contribution(self, contrib_id: str) -> bool:
        pass

    # ----------------- Charts & Insights -----------------
    @abstractmethod
    def get_daily_spending(self, month: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_monthly_trend(self, limit: int = 12) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_category_totals_for_month(self, month: str) -> List[Dict[str, Any]]:
        pass
