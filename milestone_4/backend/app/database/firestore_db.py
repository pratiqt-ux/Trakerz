"""
Cloud Firestore Implementation of BaseExpenseDatabase.
Allows Trakerz to persist expenses in Google Cloud Firestore.
"""
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.database.base import BaseExpenseDatabase


class FirestoreExpenseDatabase(BaseExpenseDatabase):
    def __init__(self, credentials_path: str, project_id: Optional[str] = None, collection_name: str = "expenses"):
        self.credentials_path = credentials_path
        self.project_id = project_id
        self.collection_name = collection_name
        self.client = None
        self.initialize()

    def initialize(self) -> None:
        try:
            from google.cloud import firestore
            from google.oauth2 import service_account
        except ImportError:
            raise RuntimeError(
                "google-cloud-firestore is not installed. Run: pip install google-cloud-firestore"
            )

        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Cloud Firestore credentials file not found: '{self.credentials_path}'. "
                "Ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid JSON service account key."
            )

        try:
            credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
            self.client = firestore.Client(
                credentials=credentials,
                project=self.project_id or credentials.project_id
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Cloud Firestore: {str(e)}")

    def _get_collection(self):
        if not self.client:
            raise RuntimeError("Firestore client is not connected.")
        return self.client.collection(self.collection_name)

    def create_expense(self, data: Dict[str, Any]) -> Dict[str, Any]:
        col = self._get_collection()
        created_at = data.get("created_at") or datetime.now().isoformat()

        doc_data = {
            "category": data["category"],
            "amount": float(data["amount"]),
            "description": data.get("description", ""),
            "date": data["date"],
            "created_at": created_at
        }

        # Add new document with auto-generated ID
        doc_ref = col.document()
        doc_ref.set(doc_data)

        doc_data["id"] = doc_ref.id
        return doc_data

    def get_expenses(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        col = self._get_collection()
        # Query order by date descending
        query = col.order_by("date", direction="DESCENDING")
        if limit:
            query = query.limit(limit)

        docs = query.stream()
        results = []
        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            item["amount"] = float(item.get("amount", 0.0))
            results.append(item)
        return results

    def get_expense(self, expense_id: str) -> Optional[Dict[str, Any]]:
        col = self._get_collection()
        doc = col.document(expense_id).get()
        if not doc.exists:
            return None
        item = doc.to_dict()
        item["id"] = doc.id
        item["amount"] = float(item.get("amount", 0.0))
        return item

    def update_expense(self, expense_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        col = self._get_collection()
        doc_ref = col.document(expense_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None

        update_fields = {}
        for key in ["category", "amount", "description", "date"]:
            if key in data and data[key] is not None:
                update_fields[key] = float(data[key]) if key == "amount" else data[key]

        if update_fields:
            doc_ref.update(update_fields)

        updated = doc_ref.get().to_dict()
        updated["id"] = expense_id
        return updated

    def delete_expense(self, expense_id: str) -> bool:
        col = self._get_collection()
        doc_ref = col.document(expense_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        doc_ref.delete()
        return True

    def get_total_expense(self) -> float:
        expenses = self.get_expenses()
        total = sum(e.get("amount", 0.0) for e in expenses)
        return round(float(total), 2)

    def get_category_totals(self) -> List[Dict[str, Any]]:
        expenses = self.get_expenses()
        total_spending = sum(e.get("amount", 0.0) for e in expenses)

        cat_map: Dict[str, Dict[str, Any]] = {}
        for e in expenses:
            cat = e.get("category", "Other")
            amt = float(e.get("amount", 0.0))
            if cat not in cat_map:
                cat_map[cat] = {"total": 0.0, "count": 0}
            cat_map[cat]["total"] += amt
            cat_map[cat]["count"] += 1

        results = []
        for cat, val in cat_map.items():
            cat_total = round(val["total"], 2)
            pct = round((cat_total / total_spending * 100), 1) if total_spending > 0 else 0.0
            results.append({
                "category": cat,
                "total": cat_total,
                "percentage": pct,
                "count": val["count"]
            })

        results.sort(key=lambda x: x["total"], reverse=True)
        return results

    def get_monthly_totals(self) -> List[Dict[str, Any]]:
        expenses = self.get_expenses()
        current_ym = datetime.now().strftime("%Y-%m")

        month_map: Dict[str, Dict[str, Any]] = {}
        for e in expenses:
            ym = e.get("date", "")[:7] or "Unknown"
            amt = float(e.get("amount", 0.0))
            if ym not in month_map:
                month_map[ym] = {"total": 0.0, "count": 0}
            month_map[ym]["total"] += amt
            month_map[ym]["count"] += 1

        results = []
        for ym, val in month_map.items():
            results.append({
                "month": ym,
                "total": round(val["total"], 2),
                "count": val["count"],
                "is_current_month": (ym == current_ym)
            })

        results.sort(key=lambda x: x["month"], reverse=True)
        return results

    def get_backend_info(self) -> Dict[str, Any]:
        return {
            "mode": "cloud",
            "database_type": "firestore",
            "status": "connected" if self.client else "disconnected",
            "project_id": self.project_id,
            "collection": self.collection_name,
            "cloud_configured": True
        }

    # Budgets, Savings Goals, and Advanced Analytics fallback implementations
    def upsert_budget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": "1", "category": data["category"], "month": data["month"], "amount": float(data["amount"]), "spent_amount": 0.0, "remaining_amount": float(data["amount"]), "percentage_used": 0.0, "status": "normal", "overspent_amount": 0.0}

    def get_budgets(self, month: Optional[str] = None) -> List[Dict[str, Any]]:
        return []

    def get_budget_by_id(self, budget_id: str) -> Optional[Dict[str, Any]]:
        return None

    def delete_budget(self, budget_id: str) -> bool:
        return False

    def create_savings_goal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": "1", "title": data["title"], "target_amount": float(data["target_amount"]), "saved_amount": 0.0, "remaining_amount": float(data["target_amount"]), "progress_percentage": 0.0, "is_completed": False, "contributions": []}

    def get_savings_goals(self) -> List[Dict[str, Any]]:
        return []

    def get_savings_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        return None

    def update_savings_goal(self, goal_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def delete_savings_goal(self, goal_id: str) -> bool:
        return False

    def add_savings_contribution(self, goal_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": "1", "goal_id": goal_id, "amount": float(data["amount"]), "note": data.get("note", ""), "date": data["date"]}

    def get_contributions_for_goal(self, goal_id: str) -> List[Dict[str, Any]]:
        return []

    def delete_savings_contribution(self, contrib_id: str) -> bool:
        return False

    def get_daily_spending(self, month: str) -> List[Dict[str, Any]]:
        return []

    def get_monthly_trend(self, limit: int = 12) -> List[Dict[str, Any]]:
        return []

    def get_category_totals_for_month(self, month: str) -> List[Dict[str, Any]]:
        return []
