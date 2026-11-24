"""
SQLite Implementation of BaseExpenseDatabase for Milestone 4.
Provides zero-configuration, persistent local storage for expenses,
monthly budgets, and savings goals. Stored strictly inside milestone_4.
"""
import sqlite3
import calendar
from datetime import datetime, date
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
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Expenses Table
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
            # 2. Budgets Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    month TEXT NOT NULL,
                    amount REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(category, month)
                )
            """)
            # 3. Savings Goals Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    deadline TEXT,
                    category TEXT DEFAULT 'General',
                    is_completed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            # 4. Savings Contributions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS savings_contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    note TEXT,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(goal_id) REFERENCES savings_goals(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    # ==========================================================
    # EXPENSES
    # ==========================================================

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

    # ==========================================================
    # BUDGETS
    # ==========================================================

    def upsert_budget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        created_at = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO budgets (category, month, amount, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(category, month) DO UPDATE SET
                    amount = excluded.amount
            """, (data["category"], data["month"], float(data["amount"]), created_at))
            conn.commit()

            cursor.execute("SELECT id, created_at FROM budgets WHERE category = ? AND month = ?",
                           (data["category"], data["month"]))
            row = cursor.fetchone()
            budget_id = str(row["id"])
            created_at = row["created_at"]

        return self.get_budget_by_id(budget_id)

    def get_budgets(self, month: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT id, category, month, amount, created_at FROM budgets"
        params = ()
        if month:
            query += " WHERE month = ?"
            params = (month,)
        query += " ORDER BY category ASC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            budget_rows = cursor.fetchall()

        results = []
        for b in budget_rows:
            cat = b["category"]
            m = b["month"]
            b_amt = float(b["amount"])

            # Compute actual spent for this category and month
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT COALESCE(SUM(amount), 0.0)
                    FROM expenses
                    WHERE category = ? AND substr(date, 1, 7) = ?
                """, (cat, m))
                spent = round(float(cur.fetchone()[0]), 2)

            remaining = round(b_amt - spent, 2)
            pct = round((spent / b_amt * 100), 1) if b_amt > 0 else 0.0
            overspent = round(spent - b_amt, 2) if spent > b_amt else 0.0

            if pct >= 100.0:
                status = "exceeded"
            elif pct >= 80.0:
                status = "warning"
            else:
                status = "normal"

            results.append({
                "id": str(b["id"]),
                "category": cat,
                "month": m,
                "amount": b_amt,
                "spent_amount": spent,
                "remaining_amount": remaining,
                "percentage_used": pct,
                "status": status,
                "overspent_amount": overspent,
                "created_at": b["created_at"]
            })
        return results

    def get_budget_by_id(self, budget_id: str) -> Optional[Dict[str, Any]]:
        try:
            int_id = int(budget_id)
        except ValueError:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, category, month, amount, created_at FROM budgets WHERE id = ?", (int_id,))
            b = cursor.fetchone()

        if not b:
            return None

        cat = b["category"]
        m = b["month"]
        b_amt = float(b["amount"])

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0.0)
                FROM expenses
                WHERE category = ? AND substr(date, 1, 7) = ?
            """, (cat, m))
            spent = round(float(cur.fetchone()[0]), 2)

        remaining = round(b_amt - spent, 2)
        pct = round((spent / b_amt * 100), 1) if b_amt > 0 else 0.0
        overspent = round(spent - b_amt, 2) if spent > b_amt else 0.0

        if pct >= 100.0:
            status = "exceeded"
        elif pct >= 80.0:
            status = "warning"
        else:
            status = "normal"

        return {
            "id": str(b["id"]),
            "category": cat,
            "month": m,
            "amount": b_amt,
            "spent_amount": spent,
            "remaining_amount": remaining,
            "percentage_used": pct,
            "status": status,
            "overspent_amount": overspent,
            "created_at": b["created_at"]
        }

    def delete_budget(self, budget_id: str) -> bool:
        try:
            int_id = int(budget_id)
        except ValueError:
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?", (int_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        return deleted

    # ==========================================================
    # SAVINGS GOALS & CONTRIBUTIONS
    # ==========================================================

    def create_savings_goal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        created_at = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO savings_goals (title, target_amount, deadline, category, is_completed, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data["title"],
                float(data["target_amount"]),
                data.get("deadline"),
                data.get("category", "General"),
                1 if data.get("is_completed") else 0,
                created_at
            ))
            conn.commit()
            goal_id = str(cursor.lastrowid)

        return self.get_savings_goal(goal_id)

    def get_savings_goals(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, target_amount, deadline, category, is_completed, created_at FROM savings_goals ORDER BY is_completed ASC, id DESC")
            rows = cursor.fetchall()

        results = []
        for r in rows:
            g_id = str(r["id"])
            goal_dict = self.get_savings_goal(g_id)
            if goal_dict:
                results.append(goal_dict)
        return results

    def get_savings_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        try:
            int_id = int(goal_id)
        except ValueError:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, target_amount, deadline, category, is_completed, created_at FROM savings_goals WHERE id = ?", (int_id,))
            r = cursor.fetchone()

        if not r:
            return None

        # Fetch contributions
        contribs = self.get_contributions_for_goal(goal_id)
        saved = round(sum(c["amount"] for c in contribs), 2)
        target = float(r["target_amount"])
        remaining = round(max(0.0, target - saved), 2)
        pct = round(min(100.0, (saved / target * 100)), 1) if target > 0 else 0.0

        # Auto complete if saved >= target
        is_completed = bool(r["is_completed"]) or (saved >= target)

        return {
            "id": str(r["id"]),
            "title": r["title"],
            "target_amount": target,
            "deadline": r["deadline"],
            "category": r["category"] or "General",
            "is_completed": is_completed,
            "saved_amount": saved,
            "remaining_amount": remaining,
            "progress_percentage": pct,
            "contributions": contribs,
            "created_at": r["created_at"]
        }

    def update_savings_goal(self, goal_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current = self.get_savings_goal(goal_id)
        if not current:
            return None

        title = data.get("title", current["title"])
        target = float(data.get("target_amount", current["target_amount"]))
        deadline = data.get("deadline", current["deadline"])
        category = data.get("category", current["category"])
        is_completed = 1 if data.get("is_completed", current["is_completed"]) else 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE savings_goals
                SET title = ?, target_amount = ?, deadline = ?, category = ?, is_completed = ?
                WHERE id = ?
            """, (title, target, deadline, category, is_completed, int(goal_id)))
            conn.commit()

        return self.get_savings_goal(goal_id)

    def delete_savings_goal(self, goal_id: str) -> bool:
        try:
            int_id = int(goal_id)
        except ValueError:
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM savings_goals WHERE id = ?", (int_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        return deleted

    def add_savings_contribution(self, goal_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            int_goal_id = int(goal_id)
        except ValueError:
            raise ValueError(f"Invalid goal_id: {goal_id}")

        created_at = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO savings_contributions (goal_id, amount, note, date, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int_goal_id,
                float(data["amount"]),
                data.get("note", ""),
                data["date"],
                created_at
            ))
            conn.commit()
            contrib_id = str(cursor.lastrowid)

        # Update completed status if goal reached
        goal = self.get_savings_goal(goal_id)
        if goal and goal["saved_amount"] >= goal["target_amount"]:
            self.update_savings_goal(goal_id, {"is_completed": True})

        return {
            "id": contrib_id,
            "goal_id": goal_id,
            "amount": float(data["amount"]),
            "note": data.get("note", ""),
            "date": data["date"],
            "created_at": created_at
        }

    def get_contributions_for_goal(self, goal_id: str) -> List[Dict[str, Any]]:
        try:
            int_id = int(goal_id)
        except ValueError:
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, goal_id, amount, note, date, created_at
                FROM savings_contributions
                WHERE goal_id = ?
                ORDER BY date DESC, id DESC
            """, (int_id,))
            rows = cursor.fetchall()

        return [
            {
                "id": str(r["id"]),
                "goal_id": str(r["goal_id"]),
                "amount": float(r["amount"]),
                "note": r["note"] or "",
                "date": r["date"],
                "created_at": r["created_at"]
            }
            for r in rows
        ]

    def delete_savings_contribution(self, contrib_id: str) -> bool:
        try:
            int_id = int(contrib_id)
        except ValueError:
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM savings_contributions WHERE id = ?", (int_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        return deleted

    # ==========================================================
    # CHARTS & INSIGHTS
    # ==========================================================

    def get_daily_spending(self, month: str) -> List[Dict[str, Any]]:
        """
        Returns all days for the given month (e.g. 2026-11)
        with day number, weekday, and spending sum.
        """
        try:
            year, m = map(int, month.split("-"))
            num_days = calendar.monthrange(year, m)[1]
        except Exception:
            num_days = 31

        # Query existing expense aggregates
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, SUM(amount) as day_total, COUNT(id) as day_count
                FROM expenses
                WHERE substr(date, 1, 7) = ?
                GROUP BY date
            """, (month,))
            db_rows = cursor.fetchall()
            rows_map = {r["date"]: (float(r["day_total"]), int(r["day_count"])) for r in db_rows}

        days_data = []
        for day in range(1, num_days + 1):
            date_str = f"{month}-{day:02d}"
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = dt.strftime("%a")
            except Exception:
                day_name = ""

            amt, cnt = rows_map.get(date_str, (0.0, 0))
            days_data.append({
                "date": date_str,
                "day": day,
                "day_name": day_name,
                "amount": round(amt, 2),
                "transaction_count": cnt
            })

        return days_data

    def get_monthly_trend(self, limit: int = 12) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT substr(date, 1, 7) as month_ym, SUM(amount) as month_total, COUNT(id) as count
                FROM expenses
                GROUP BY month_ym
                ORDER BY month_ym ASC
            """)
            rows = cursor.fetchall()

        results = []
        for r in rows:
            ym = r["month_ym"]
            try:
                dt = datetime.strptime(ym, "%Y-%m")
                display = dt.strftime("%b %Y")
            except Exception:
                display = ym
            results.append({
                "month": ym,
                "display_name": display,
                "amount": round(float(r["month_total"]), 2),
                "transaction_count": int(r["count"])
            })

        if limit and len(results) > limit:
            results = results[-limit:]
        return results

    def get_category_totals_for_month(self, month: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, SUM(amount) as cat_total, COUNT(id) as cat_count
                FROM expenses
                WHERE substr(date, 1, 7) = ?
                GROUP BY category
                ORDER BY cat_total DESC
            """, (month,))
            rows = cursor.fetchall()

        month_total = sum(float(r["cat_total"]) for r in rows)
        results = []
        for r in rows:
            amt = round(float(r["cat_total"]), 2)
            pct = round((amt / month_total * 100), 1) if month_total > 0 else 0.0
            results.append({
                "category": r["category"],
                "total": amt,
                "percentage": pct,
                "count": int(r["cat_count"])
            })
        return results
