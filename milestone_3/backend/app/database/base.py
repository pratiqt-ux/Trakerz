"""
Base Database Interface.
Defines the abstract contract that any storage backend (SQLite, Cloud Firestore)
must implement.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseExpenseDatabase(ABC):
    """Abstract interface for Trakerz storage engines."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize database connection, schema or collections."""
        pass

    @abstractmethod
    def create_expense(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new expense and return it with assigned ID."""
        pass

    @abstractmethod
    def get_expenses(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve all expenses sorted by date/creation descending."""
        pass

    @abstractmethod
    def get_expense(self, expense_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single expense by ID."""
        pass

    @abstractmethod
    def update_expense(self, expense_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing expense by ID."""
        pass

    @abstractmethod
    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense by ID. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    def get_total_expense(self) -> float:
        """Calculate total amount of all expenses."""
        pass

    @abstractmethod
    def get_category_totals(self) -> List[Dict[str, Any]]:
        """Return list of categories with totals, percentages, and counts."""
        pass

    @abstractmethod
    def get_monthly_totals(self) -> List[Dict[str, Any]]:
        """Return spending aggregated by month."""
        pass

    @abstractmethod
    def get_backend_info(self) -> Dict[str, Any]:
        """Return metadata about current storage engine."""
        pass
