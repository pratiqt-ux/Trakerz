"""
Comprehensive Automated Test Suite for Trakerz Milestone 5.
Tests all 5 new AI & Financial Intelligence features plus Milestone 4 regression.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
import httpx

# Setup paths strictly inside milestone_5
TEST_DIR = Path(__file__).resolve().parent
M5_DIR = TEST_DIR.parent
BACKEND_DIR = M5_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

TEST_DB_PATH = BACKEND_DIR / "test_m5_suite.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["STORAGE_MODE"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "test_m5_suite.db"

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
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

    print("=" * 70)
    print("TRAKERZ MILESTONE 5: AI & INTELLIGENCE TEST SUITE")
    print("=" * 70)

    now = datetime.now()
    cur_month = now.strftime("%Y-%m")
    today_str = now.strftime("%Y-%m-%d")

    # -------------------------------------------------------------
    # 1. FORECAST & ANOMALY ON EMPTY / INSUFFICIENT DATA
    # -------------------------------------------------------------
    print("\n--- 1. Insufficient Data Guards ---")
    res = client.get(f"/api/analytics/forecast?month={cur_month}")
    f_empty = res.json()
    test(
        res.status_code == 200 and f_empty["confidence_level"] == "insufficient_data" and f_empty["estimated_month_end_spending"] == 0.0,
        "1.1 Forecast handles 0 expenses cleanly (insufficient_data)"
    )

    res = client.get("/api/analytics/anomalies")
    test(
        res.status_code == 200 and len(res.json()) == 0,
        "1.2 Anomaly detection produces 0 false alerts with empty DB"
    )

    # -------------------------------------------------------------
    # 2. SMART EXPENSE CATEGORIZATION
    # -------------------------------------------------------------
    print("\n--- 2. Smart Expense Categorization ---")
    res = client.post("/api/ai/categorize", json={"description": "Dominos pizza 450", "amount": 450})
    c1 = res.json()
    test(
        res.status_code == 200 and c1["suggested_category"] == "Food" and c1["suggested_description"] == "Dominos pizza",
        f"2.1 Food categorization ('Dominos pizza 450' -> {c1.get('suggested_category')}, '{c1.get('suggested_description')}')"
    )

    res = client.post("/api/ai/categorize", json={"description": "Uber ride to college 180", "amount": 180})
    c2 = res.json()
    test(
        res.status_code == 200 and c2["suggested_category"] == "Travel",
        f"2.2 Travel categorization ('Uber ride to college 180' -> {c2.get('suggested_category')})"
    )

    res = client.post("/api/ai/categorize", json={"description": "Xyzabc unknown vendor"})
    c3 = res.json()
    test(
        res.status_code == 200 and c3["suggested_category"] == "Other" and c3["confidence"] == "low",
        "2.3 Unrecognized description falls back safely to Other (low confidence)"
    )

    # -------------------------------------------------------------
    # 3. POPULATE HISTORICAL DATA & TEST ANOMALIES + FORECAST + INSIGHTS
    # -------------------------------------------------------------
    print("\n--- 3. Historical Data, Anomaly Detection & Forecast ---")
    # Add 4 normal Food expenses on past days (avg ~ ₹150/day)
    for i in range(1, 5):
        past_dt = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        client.post("/api/expenses", json={"category": "Food", "amount": 150.0, "date": past_dt, "description": f"Lunch day -{i}"})

    # Normal transaction today (₹160) -> should NOT trigger daily spike (< 1.8x)
    client.post("/api/expenses", json={"category": "Food", "amount": 160.0, "date": today_str, "description": "Normal canteen meal"})
    res = client.get("/api/analytics/anomalies")
    test(len(res.json()) == 0, "3.1 Normal Food expense (₹160 vs ₹150 avg) does not trigger false anomaly")

    # Add a huge Food spike today (₹600 -> total today ₹760 = 5.1x usual ₹150 avg!)
    client.post("/api/expenses", json={"category": "Food", "amount": 600.0, "date": today_str, "description": "Big group dinner"})
    res = client.get("/api/analytics/anomalies")
    anoms = res.json()
    test(
        len(anoms) >= 1 and any(a["anomaly_type"] == "daily_category_spike" and a["category"] == "Food" for a in anoms),
        f"3.2 Daily category spike detected ({anoms[0]['message'] if anoms else 'none'})"
    )

    # Forecast with data
    res = client.get(f"/api/analytics/forecast?month={cur_month}")
    f_data = res.json()
    test(
        res.status_code == 200 and f_data["current_spending"] > 0 and f_data["estimated_month_end_spending"] >= f_data["current_spending"] and f_data["is_estimate"] is True and len(f_data["projected_series"]) >= 28,
        f"3.3 Monthly forecast computed (current ₹{f_data['current_spending']}, est ₹{f_data['estimated_month_end_spending']})"
    )

    # -------------------------------------------------------------
    # 4. AI FINANCIAL CHAT ASSISTANT
    # -------------------------------------------------------------
    print("\n--- 4. AI Financial Chat Assistant ---")
    # 4.1 Empty chat input rejected
    res = client.post("/api/ai/chat", json={"message": "   "})
    test(res.status_code == 422, "4.1 Empty chat input rejected (Status 422)")

    # 4.2 Unconfigured API key handled gracefully
    orig_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = ""
    res = client.get("/api/ai/status")
    test(res.status_code == 200 and res.json()["ai_configured"] is False, "4.2 AI status reports unconfigured when key missing")

    res = client.post("/api/ai/chat", json={"message": "How much did I spend this month?"})
    chat_unconf = res.json()
    test(
        res.status_code == 200 and chat_unconf["ai_available"] is False and chat_unconf["error_type"] == "not_configured",
        "4.3 Unconfigured AI key returns honest not_configured message (no fake AI)"
    )

    # 4.4 Mocked Valid Gemini API response + verify real user financial context is sent
    settings.GEMINI_API_KEY = "test_fake_key_1234567890"
    captured_payloads = []

    class MockResp:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data

        def json(self):
            return self._json

    async def mock_post_success(self, url, headers=None, json=None):
        captured_payloads.append(json)
        return MockResp(200, {
            "candidates": [{"content": {"parts": [{"text": "You have spent ₹1,360.00 across 6 expenses, mostly on Food."}]}}]
        })

    with patch.object(httpx.AsyncClient, "post", new=mock_post_success):
        res = client.post("/api/ai/chat", json={"message": "How much did I spend?"})
        chat_ok = res.json()
        sys_text = captured_payloads[0]["system_instruction"]["parts"][0]["text"] if captured_payloads else ""
        test(
            res.status_code == 200 and chat_ok["ai_available"] is True and "Food" in sys_text and "1360.0" in sys_text,
            "4.4 AI chat sends summarized real Trakerz data to Gemini and returns AI reply"
        )

    # 4.5 Invalid API key (401)
    async def mock_post_invalid(self, url, headers=None, json=None):
        return MockResp(401, {"error": {"message": "API key not valid"}})

    with patch.object(httpx.AsyncClient, "post", new=mock_post_invalid):
        res = client.post("/api/ai/chat", json={"message": "Hello?"})
        chat_err = res.json()
        test(
            res.status_code == 200 and chat_err["ai_available"] is False and chat_err["error_type"] == "invalid_key",
            "4.5 Invalid API key (HTTP 401) handled gracefully"
        )

    # 4.6 Network failure / offline
    async def mock_post_network_err(self, url, headers=None, json=None):
        raise httpx.ConnectError("Network unreachable")

    with patch.object(httpx.AsyncClient, "post", new=mock_post_network_err):
        res = client.post("/api/ai/chat", json={"message": "Hello?"})
        chat_net = res.json()
        test(
            res.status_code == 200 and chat_net["ai_available"] is False and chat_net["error_type"] == "network_error",
            "4.6 Network failure handled gracefully without crashing"
        )

    settings.GEMINI_API_KEY = orig_key

    # -------------------------------------------------------------
    # 5. MILESTONE 4 REGRESSION & STATIC ASSETS
    # -------------------------------------------------------------
    print("\n--- 5. Milestone 4 Regression & UI Assets ---")
    # Budget + Alert
    res = client.post("/api/budgets", json={"category": "Food", "month": cur_month, "amount": 1000.0})
    test(res.status_code == 201 and res.json()["status"] == "exceeded", "5.1 Budgets & 100% exceeded alert still work")

    # Savings Goal + Contribution
    res = client.post("/api/savings-goals", json={"title": "Emergency Fund", "target_amount": 10000.0})
    gid = res.json()["id"]
    res = client.post(f"/api/savings-goals/{gid}/contribute", json={"amount": 2500.0, "date": today_str})
    test(res.status_code == 201, "5.2 Savings goals & contributions still work")

    # Personalized Insights
    res = client.get(f"/api/analytics/insights?month={cur_month}")
    test(res.status_code == 200 and len(res.json()) >= 1, "5.3 Personalized insights generated")

    # UI Static Assets
    res_html = client.get("/")
    res_css = client.get("/static/css/style.css")
    res_js = client.get("/static/js/app.js")
    res_sw = client.get("/service-worker.js")
    test(
        res_html.status_code == 200 and "AI Suite M5" in res_html.text and "view-assistant" in res_html.text,
        "5.4 Milestone 5 index.html includes AI Assistant & Forecast UI"
    )
    test(
        res_css.status_code == 200 and ".chat-shell" in res_css.text and res_js.status_code == 200 and "sendChatMessage" in res_js.text and "trakerz-shell-v5" in res_sw.text,
        "5.5 Milestone 5 CSS, JS, and Service Worker v5 served properly"
    )

    # Cleanup
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

    print("\n" + "=" * 70)
    print(f"MILESTONE 5 TEST RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_suite()
