"""
SQLite Implementation of BaseExpenseDatabase.
Uses SQLite for zero-configuration, persistent local storage.
Kept strictly inside milestone_3.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.database.base import BaseExpenseDatabase


class SQLiteExpenseDatabase(BaseExpenseDatabase):
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.initialize()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_expense(self, data: Dict[str, Any]) -> Dict[str, Any]:
        created_at = data.get("created_at") or datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (category, amount, description, date, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data["category"],
                float(data["amount"]),
                data.get("description", ""),
                data["date"],
                created_at
            ))
            conn.commit()
            new_id = str(cursor.lastrowid)

        return {
            "id": new_id,
            "category": data["category"],
            "amount": float(data["amount"]),
            "description": data.get("description", ""),
            "date": data["date"],
            "created_at": created_at
        }

    def get_expenses(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = "SELECT id, category, amount, description, date, created_at FROM expenses ORDER BY date DESC, id DESC"
        params = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [
            {
                "id": str(r["id"]),
                "category": r["category"],
                "amount": float(r["amount"]),
                "description": r["description"] or "",
                "date": r["date"],
                "created_at": r["created_at"]
            }
            for r in rows
        ]

    def get_expense(self, expense_id: str) -> Optional[Dict[str, Any]]:
        try:
            int_id = int(expense_id)
        except ValueError:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, category, amount, description, date, created_at FROM expenses WHERE id = ?", (int_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": str(row["id"]),
            "category": row["category"],
            "amount": float(row["amount"]),
            "description": row["description"] or "",
            "date": row["date"],
            "created_at": row["created_at"]
        }

    def update_expense(self, expense_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current = self.get_expense(expense_id)
        if not current:
            return None

        new_category = data.get("category", current["category"])
        new_amount = float(data.get("amount", current["amount"]))
        new_description = data.get("description", current["description"])
        new_date = data.get("date", current["date"])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE expenses
                SET category = ?, amount = ?, description = ?, date = ?
                WHERE id = ?
            """, (new_category, new_amount, new_description, new_date, int(expense_id)))
            conn.commit()

        return {
            "id": expense_id,
            "category": new_category,
            "amount": new_amount,
            "description": new_description,
            "date": new_date,
            "created_at": current["created_at"]
        }

    def delete_expense(self, expense_id: str) -> bool:
        try:
            int_id = int(expense_id)
        except ValueError:
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (int_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        return deleted

    def get_total_expense() -> float:
        pass

    def get_total_expense(self) -> float:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses")
            row = cursor.fetchone()
            total = float(row[0]) if row else 0.0
        return round(total, 2)

    def get_category_totals(self) -> List[Dict[str, Any]]:
        total_spending = self.get_total_expense()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, SUM(amount) as cat_total, COUNT(id) as cat_count
                FROM expenses
                GROUP BY category
                ORDER BY cat_total DESC
            """)
            rows = cursor.fetchall()

        results = []
        for r in rows:
            cat_total = round(float(r["cat_total"]), 2)
            pct = round((cat_total / total_spending * 100), 1) if total_spending > 0 else 0.0
            results.append({
                "category": r["category"],
                "total": cat_total,
                "percentage": pct,
                "count": int(r["cat_count"])
            })
        return results

    def get_monthly_totals(self) -> List[Dict[str, Any]]:
        current_ym = datetime.now().strftime("%Y-%m")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT substr(date, 1, 7) as month_ym, SUM(amount) as month_total, COUNT(id) as month_count
                FROM expenses
                GROUP BY month_ym
                ORDER BY month_ym DESC
            """)
            rows = cursor.fetchall()

        results = []
        for r in rows:
            ym = r["month_ym"]
            results.append({
                "month": ym,
                "total": round(float(r["month_total"]), 2),
                "count": int(r["month_count"]),
                "is_current_month": (ym == current_ym)
            })
        return results

    def get_backend_info(self) -> Dict[str, Any]:
        return {
            "mode": "local",
            "database_type": "sqlite",
            "status": "connected",
            "file": str(self.db_path.name),
            "cloud_configured": False
        }
