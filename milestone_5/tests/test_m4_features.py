"""
Comprehensive Automated Test Suite for Trakerz Milestone 4.
Validates:
- Expenses CRUD & Persistence
- Category Budgets, 80% Warnings & 100% Exceeded Alerts
- Savings Goals, Deposit Contributions & Goal Completion
- Chart Analytics (Daily, Monthly Trend, Category Breakdown)
- Month-over-Month (MoM) Algorithmic Financial Insights
- Dashboard Overview Aggregation
- Static Assets & Offline Vendor Chart.js Serving
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Setup paths strictly in milestone_4
TEST_DIR = Path(__file__).resolve().parent
M4_DIR = TEST_DIR.parent
BACKEND_DIR = M4_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Use isolated test database in milestone_4
TEST_DB_PATH = BACKEND_DIR / "test_m4_suite.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["STORAGE_MODE"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "test_m4_suite.db"

from fastapi.testclient import TestClient
from app.main import app
from app.database.sqlite_db import SQLiteExpenseDatabase
import app.database as db_module

# Override database singleton
test_db = SQLiteExpenseDatabase(TEST_DB_PATH)
db_module._db_instance = test_db

client = TestClient(app)

def run_suite():
    passed = 0
    failed = 0

    def test(condition, name, detail=""):
        nonlocal passed, failed
        if condition:
            print(f" [PASS] {name}")
            passed += 1
        else:
            print(f" [FAIL] {name} | {detail}")
            failed += 1

    print("=" * 65)
    print("TRAKERZ MILESTONE 4: FULL FEATURE & REGRESSION TEST SUITE")
    print("=" * 65)

    current_month = datetime.now().strftime("%Y-%m")
    today_str = datetime.now().strftime("%Y-%m-%d")

    # -------------------------------------------------------------
    # 1. EXPENSES CRUD & BASIC ANALYTICS
    # -------------------------------------------------------------
    print("\n--- 1. Expenses & Validation ---")
    res = client.post("/api/expenses", json={"category": "", "amount": -10, "date": "invalid"})
    test(res.status_code == 422, "1.1 Reject invalid expense payload")

    # Add Food expense #1: ₹400
    res = client.post("/api/expenses", json={"category": "Food", "amount": 400.0, "date": today_str, "description": "Lunch"})
    exp1 = res.json()
    test(res.status_code == 201 and exp1["amount"] == 400.0, "1.2 Add valid Food expense (₹400.00)")

    # Add Travel expense: ₹250
    res = client.post("/api/expenses", json={"category": "Travel", "amount": 250.0, "date": today_str, "description": "Taxi"})
    exp2 = res.json()
    test(res.status_code == 201 and exp2["amount"] == 250.0, "1.3 Add valid Travel expense (₹250.00)")

    # List expenses
    res = client.get("/api/expenses")
    test(res.status_code == 200 and len(res.json()) == 2, "1.4 List all expenses")

    # Total analytics
    res = client.get("/api/analytics/total")
    test(res.status_code == 200 and res.json()["total_amount"] == 650.0, "1.5 Total spending calculation (₹650.00)")

    # -------------------------------------------------------------
    # 2. CATEGORY BUDGETS & ALERT SYSTEM
    # -------------------------------------------------------------
    print("\n--- 2. Category Budgets & Alert System ---")
    # Set Food budget to ₹1,000 (currently ₹400 spent = 40% -> normal)
    res = client.post("/api/budgets", json={"category": "Food", "month": current_month, "amount": 1000.0})
    b_food = res.json()
    test(
        res.status_code == 201 and b_food["spent_amount"] == 400.0 and b_food["remaining_amount"] == 600.0 and b_food["status"] == "normal",
        "2.1 Create Food budget (₹1,000 limit, 40% used -> normal)"
    )

    # Set Travel budget to ₹300 (currently ₹250 spent = 83.3% -> WARNING alert)
    res = client.post("/api/budgets", json={"category": "Travel", "month": current_month, "amount": 300.0})
    b_travel = res.json()
    test(
        res.status_code == 201 and b_travel["spent_amount"] == 250.0 and b_travel["status"] == "warning" and b_travel["percentage_used"] >= 80.0,
        "2.2 80% Budget Warning Triggered (Travel 83.3% used -> warning)"
    )

    # Verify Warning Alert in alerts endpoint
    res = client.get(f"/api/budgets/alerts?month={current_month}")
    alerts = res.json()
    travel_alert = next((a for a in alerts if a["category"] == "Travel"), None)
    test(travel_alert is not None and travel_alert["alert_type"] == "warning", "2.3 Budget Warning Alert returned in /api/budgets/alerts")

    # Add more Food expense to EXCEED budget: add ₹700 (total spent = ₹1,100 of ₹1,000 limit -> 110% EXCEEDED)
    res = client.post("/api/expenses", json={"category": "Food", "amount": 700.0, "date": today_str, "description": "Dinner feast"})
    test(res.status_code == 201, "2.4 Added ₹700 to Food")

    # Verify Food budget status is now EXCEEDED
    res = client.get(f"/api/budgets/{b_food['id']}")
    b_food_updated = res.json()
    test(
        b_food_updated["status"] == "exceeded" and b_food_updated["overspent_amount"] == 100.0 and b_food_updated["spent_amount"] == 1100.0,
        "2.5 100% Budget Exceeded Triggered (Food spent ₹1,100 of ₹1,000 -> overspent ₹100.00)"
    )

    # Edit Budget Limit: update Food budget to ₹2,000 (status should return to normal)
    res = client.put(f"/api/budgets/{b_food['id']}", json={"amount": 2000.0})
    test(res.status_code == 200 and res.json()["status"] == "normal" and res.json()["amount"] == 2000.0, "2.6 Edit Budget Limit to ₹2,000 (status returns to normal)")

    # Delete Budget
    res = client.delete(f"/api/budgets/{b_travel['id']}")
    test(res.status_code == 200, "2.7 Delete Travel budget")

    # -------------------------------------------------------------
    # 3. SAVINGS GOALS & CONTRIBUTIONS
    # -------------------------------------------------------------
    print("\n--- 3. Savings Goals & Contributions ---")
    # Create Goal: New Laptop (Target: ₹50,000)
    goal_payload = {
        "title": "New Laptop",
        "target_amount": 50000.0,
        "deadline": "2026-12-31",
        "category": "Tech"
    }
    res = client.post("/api/savings-goals", json=goal_payload)
    goal1 = res.json()
    test(
        res.status_code == 201 and goal1["title"] == "New Laptop" and goal1["saved_amount"] == 0.0 and not goal1["is_completed"],
        "3.1 Create Savings Goal (Target: ₹50,000.00)"
    )

    # Add Contribution #1: ₹20,000
    contrib1_payload = {
        "amount": 20000.0,
        "note": "Initial deposit",
        "date": today_str
    }
    res = client.post(f"/api/savings-goals/{goal1['id']}/contribute", json=contrib1_payload)
    test(res.status_code == 201 and res.json()["amount"] == 20000.0, "3.2 Add Contribution #1 (₹20,000.00)")

    # Verify Progress Calculation
    res = client.get(f"/api/savings-goals/{goal1['id']}")
    g_info = res.json()
    test(
        g_info["saved_amount"] == 20000.0 and g_info["remaining_amount"] == 30000.0 and g_info["progress_percentage"] == 40.0,
        "3.3 Goal Progress Calculation (₹20,000 saved, ₹30,000 remaining, 40% progress)"
    )

    # Add Contribution #2 to COMPLETE the goal: ₹30,000
    res = client.post(f"/api/savings-goals/{goal1['id']}/contribute", json={"amount": 30000.0, "date": today_str, "note": "Bonus"})
    test(res.status_code == 201, "3.4 Add Contribution #2 (₹30,000.00)")

    # Verify Goal is marked Completed
    res = client.get(f"/api/savings-goals/{goal1['id']}")
    g_completed = res.json()
    test(
        g_completed["is_completed"] and g_completed["saved_amount"] == 50000.0 and g_completed["progress_percentage"] == 100.0,
        "3.5 Auto-mark Goal Completed (100% reached)"
    )

    # Edit Goal details
    res = client.put(f"/api/savings-goals/{goal1['id']}", json={"category": "Hardware"})
    test(res.status_code == 200 and res.json()["category"] == "Hardware", "3.6 Edit Savings Goal details")

    # -------------------------------------------------------------
    # 4. CHARTS & ANALYTICS DATA
    # -------------------------------------------------------------
    print("\n--- 4. Chart.js Analytics Endpoints ---")
    # Chart A: Category Spending in Month
    res = client.get(f"/api/analytics/category-month?month={current_month}")
    cat_chart = res.json()
    test(
        res.status_code == 200 and len(cat_chart) >= 2 and any(c["category"] == "Food" for c in cat_chart),
        "4.1 Chart A: Category Spending breakdown returned"
    )

    # Chart B: Monthly Trend
    res = client.get("/api/analytics/monthly-trend")
    month_chart = res.json()
    test(
        res.status_code == 200 and len(month_chart) >= 1 and month_chart[-1]["month"] == current_month,
        "4.2 Chart B: Monthly Trend history returned"
    )

    # Chart C: Daily Spending
    res = client.get(f"/api/analytics/daily?month={current_month}")
    daily_chart = res.json()
    test(
        res.status_code == 200 and len(daily_chart) >= 28 and any(d["amount"] > 0 for d in daily_chart),
        "4.3 Chart C: Daily spending breakdown for all days returned"
    )

    # -------------------------------------------------------------
    # 5. SMART MONTH-OVER-MONTH INSIGHTS
    # -------------------------------------------------------------
    print("\n--- 5. Month-over-Month (MoM) Financial Insights ---")
    res = client.get(f"/api/analytics/insights?month={current_month}")
    insights = res.json()
    test(
        res.status_code == 200 and len(insights) >= 1 and all("title" in i and "description" in i for i in insights),
        "5.1 MoM algorithmic insights generated successfully"
    )

    # Dashboard Overview Aggregation
    res = client.get("/api/analytics/dashboard-overview")
    dash = res.json()
    test(
        res.status_code == 200 and dash["this_month_spending"] > 0 and "recent_transactions" in dash,
        "5.2 Dashboard Overview endpoint returned aggregated KPIs"
    )

    # -------------------------------------------------------------
    # 6. STATIC ASSETS & VENDOR CHART.JS SERVING
    # -------------------------------------------------------------
    print("\n--- 6. Static Assets & Vendor Bundle ---")
    res = client.get("/")
    test(res.status_code == 200 and "AI Suite M5" in res.text, "6.1 Modernized index.html served at root")

    res = client.get("/static/css/style.css")
    test(res.status_code == 200 and "--sidebar-width" in res.text, "6.2 Modern CSS with desktop sidebar & bottom bar served")

    res = client.get("/static/js/app.js")
    test(res.status_code == 200 and "renderCategoryChart" in res.text, "6.3 Milestone 5 JavaScript served")

    res = client.get("/static/js/vendor/chart.umd.min.js")
    test(res.status_code == 200 and len(res.content) > 100000, "6.4 Locally bundled Chart.js vendor script served")

    res = client.get("/service-worker.js")
    test(res.status_code == 200 and "trakerz-shell-v5" in res.text, "6.5 Service worker with v5 shell caching served")

    # -------------------------------------------------------------
    # 7. DATA PERSISTENCE ACROSS SERVER RESTART
    # -------------------------------------------------------------
    print("\n--- 7. Database Persistence ---")
    # Reconnect fresh database instance to simulate server restart
    reconnect_db = SQLiteExpenseDatabase(TEST_DB_PATH)
    persisted_expenses = reconnect_db.get_expenses()
    persisted_budgets = reconnect_db.get_budgets()
    persisted_goals = reconnect_db.get_savings_goals()

    test(
        len(persisted_expenses) == 3 and len(persisted_budgets) >= 1 and len(persisted_goals) >= 1,
        "7.1 Full persistence across connection reconnect (Expenses, Budgets, Savings Goals preserved)"
    )

    # Cleanup test db
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

    print("\n" + "=" * 65)
    print(f"MILESTONE 4 TEST RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 65)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_suite()
