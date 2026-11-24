"""
End-to-End Test Suite for Trakerz Milestone 4 Baseline.
Verifies all REST API endpoints, validation rules, static asset serving,
and database persistence.
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
TEST_DIR = Path(__file__).resolve().parent
M4_DIR = TEST_DIR.parent
BACKEND_DIR = M4_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Use isolated test database inside milestone_4
TEST_DB_PATH = BACKEND_DIR / "test_trakerz_m4.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["STORAGE_MODE"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "test_trakerz_m4.db"

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.database.sqlite_db import SQLiteExpenseDatabase
import app.database as db_module

# Override database for testing
test_db = SQLiteExpenseDatabase(TEST_DB_PATH)
db_module._db_instance = test_db

client = TestClient(app)

def run_tests():
    passed = 0
    failed = 0

    def assert_test(condition, name, detail=""):
        nonlocal passed, failed
        if condition:
            print(f" [PASS] {name}")
            passed += 1
        else:
            print(f" [FAIL] {name}: {detail}")
            failed += 1

    print("=" * 60)
    print("RUNNING TRAKERZ MILESTONE 4 BASELINE TEST SUITE")
    print("=" * 60)

    # 1. Health Endpoint
    res = client.get("/api/health")
    assert_test(res.status_code == 200 and res.json().get("status") == "healthy", "1. Health Endpoint Check")

    # 2. Status Endpoint
    res = client.get("/api/status")
    data = res.json()
    assert_test(res.status_code == 200 and data.get("mode") == "local" and data.get("database") == "sqlite", "2. System Status Endpoint (Local Mode)")

    # 3. Validation: Reject Negative Amount
    res = client.post("/api/expenses", json={"category": "Food", "amount": -50.0, "date": "2026-11-24"})
    assert_test(res.status_code == 422, "3. Reject Negative Amount (Status 422)")

    # 4. Validation: Reject Zero Amount
    res = client.post("/api/expenses", json={"category": "Food", "amount": 0.0, "date": "2026-11-24"})
    assert_test(res.status_code == 422, "4. Reject Zero Amount (Status 422)")

    # 5. Validation: Reject Empty Category
    res = client.post("/api/expenses", json={"category": "   ", "amount": 100.0, "date": "2026-11-24"})
    assert_test(res.status_code == 422, "5. Reject Empty Category (Status 422)")

    # 6. Validation: Reject Invalid Date
    res = client.post("/api/expenses", json={"category": "Food", "amount": 100.0, "date": "not-a-date"})
    assert_test(res.status_code == 422, "6. Reject Invalid Date (Status 422)")

    # 7. Add Valid Expense #1 (Food)
    exp1_payload = {
        "category": "Food",
        "amount": 250.50,
        "description": "Lunch at college canteen",
        "date": "2026-11-24"
    }
    res = client.post("/api/expenses", json=exp1_payload)
    exp1 = res.json()
    assert_test(
        res.status_code == 201 and exp1.get("amount") == 250.50 and exp1.get("category") == "Food" and "id" in exp1,
        "7. Add Valid Expense #1 (Food, ₹250.50)"
    )

    # 8. Add Valid Expense #2 (Travel)
    exp2_payload = {
        "category": "Travel",
        "amount": 120.00,
        "description": "Metro recharge",
        "date": "2026-11-24"
    }
    res = client.post("/api/expenses", json=exp2_payload)
    exp2 = res.json()
    assert_test(
        res.status_code == 201 and exp2.get("amount") == 120.00 and exp2.get("category") == "Travel",
        "8. Add Valid Expense #2 (Travel, ₹120.00)"
    )

    # 9. Retrieve Expense By ID
    res = client.get(f"/api/expenses/{exp1['id']}")
    assert_test(
        res.status_code == 200 and res.json().get("description") == "Lunch at college canteen",
        "9. Retrieve Single Expense by ID"
    )

    # 10. List All Expenses
    res = client.get("/api/expenses")
    expenses_list = res.json()
    assert_test(
        res.status_code == 200 and len(expenses_list) == 2,
        "10. List All Expenses (Count = 2)"
    )

    # 11. Total Summary Analytics
    res = client.get("/api/analytics/total")
    total_data = res.json()
    assert_test(
        res.status_code == 200 and total_data.get("total_amount") == 370.50 and total_data.get("expense_count") == 2,
        f"11. Total Analytics Sum (Expected: 370.50, Got: {total_data.get('total_amount')})"
    )

    # 12. Category Analytics Breakdown
    res = client.get("/api/analytics/categories")
    cat_data = res.json()
    food_cat = next((c for c in cat_data if c["category"] == "Food"), None)
    travel_cat = next((c for c in cat_data if c["category"] == "Travel"), None)
    assert_test(
        food_cat is not None and travel_cat is not None and food_cat["total"] == 250.50 and travel_cat["total"] == 120.00,
        "12. Category Breakdown Analytics"
    )

    # 13. Monthly Analytics Breakdown
    res = client.get("/api/analytics/monthly")
    monthly_data = res.json()
    assert_test(
        res.status_code == 200 and len(monthly_data) >= 1 and monthly_data[0]["total"] == 370.50,
        "13. Monthly Summary Analytics"
    )

    # 14. Update Expense
    res = client.put(f"/api/expenses/{exp2['id']}", json={"amount": 150.00, "description": "Metro recharge updated"})
    assert_test(
        res.status_code == 200 and res.json().get("amount") == 150.00 and res.json().get("description") == "Metro recharge updated",
        "14. Update Expense Amount & Description"
    )

    # 15. Verify Updated Total (250.50 + 150.00 = 400.50)
    res = client.get("/api/analytics/total")
    assert_test(
        res.json().get("total_amount") == 400.50,
        "15. Analytics Reflects Updated Amount (₹400.50)"
    )

    # 16. Delete Expense #2
    res = client.delete(f"/api/expenses/{exp2['id']}")
    assert_test(res.status_code == 200, "16. Delete Expense by ID")

    # 17. Verify Expense is Gone
    res = client.get(f"/api/expenses/{exp2['id']}")
    assert_test(res.status_code == 404, "17. Non-Existent Expense Returns 404")

    # 18. Verify List Count is Now 1 and Total is 250.50
    res = client.get("/api/expenses")
    res_tot = client.get("/api/analytics/total")
    assert_test(
        len(res.json()) == 1 and res_tot.json().get("total_amount") == 250.50,
        "18. Database State After Deletion"
    )

    # 19. Static Files: Mobile Index HTML
    res = client.get("/")
    assert_test(
        res.status_code == 200 and "Trakerz" in res.text and "<!DOCTYPE html>" in res.text,
        "19. Mobile App Index HTML Served at Root"
    )

    # 20. Static Files: CSS
    res = client.get("/static/css/style.css")
    assert_test(res.status_code == 200 and "--accent-primary" in res.text, "20. Mobile CSS Served")

    # 21. Static Files: JavaScript
    res = client.get("/static/js/app.js")
    assert_test(res.status_code == 200 and "loadAllData" in res.text, "21. Mobile JavaScript Served")

    # 22. Static Files: Manifest & Service Worker
    res_m = client.get("/manifest.json")
    res_sw = client.get("/service-worker.js")
    assert_test(
        res_m.status_code == 200 and res_sw.status_code == 200 and "standalone" in res_m.text,
        "22. PWA Manifest & Service Worker Served"
    )

    # 23. Data Persistence Across Connection Re-instantiation (Simulate Server Restart)
    reconnected_db = SQLiteExpenseDatabase(TEST_DB_PATH)
    persisted_expenses = reconnected_db.get_expenses()
    persisted_total = reconnected_db.get_total_expense()
    assert_test(
        len(persisted_expenses) == 1 and persisted_total == 250.50 and persisted_expenses[0]["category"] == "Food",
        "23. Data Persistence Across Database Reconnect"
    )

    # Clean up test database
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

    print("=" * 60)
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
