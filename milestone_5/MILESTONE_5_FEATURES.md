# Trakerz Milestone 5 — AI & Financial Intelligence Architecture

This document explains how each of Milestone 5's five intelligence features works under the hood.

---

## 1. AI Financial Chat Assistant
- **Service:** `backend/app/services/ai_chat_service.py`
- **Endpoint:** `POST /api/ai/chat` & `GET /api/ai/status`
- **Privacy & Grounding:**
  - Never exposes `GEMINI_API_KEY` to the frontend browser.
  - Never dumps the entire raw database to the AI provider; instead, `_build_financial_context()` builds a compact JSON summary containing current/previous month totals, category totals, budgets, savings goals, forecast estimate, anomaly messages, and up to 20 recent transactions.
  - System prompt strictly instructs the model to use only provided figures, state when data is insufficient, and never claim to perform write actions.

## 2. Smart Expense Categorization
- **Service:** `backend/app/services/categorization_service.py`
- **Endpoint:** `POST /api/ai/categorize`
- **How it works:**
  1. Strips trailing amounts from raw descriptions (e.g., `"Dominos pizza 450"` &rarr; `"Dominos pizza"`).
  2. Checks deterministic keyword rules (`Food`, `Travel`, `Groceries`, `Bills`, `Shopping`, `Entertainment`, `Health`, `Education`).
  3. Maps canonical categories to existing user categories in the database via `CATEGORY_ALIASES` (e.g., if the user already uses `"Transport"`, it suggests `"Transport"` instead of creating a duplicate `"Travel"`).
  4. If no local keyword matches and `GEMINI_API_KEY` is configured, optionally queries Gemini; otherwise defaults safely to `"Other"`.
  5. Users can manually override the suggestion at any time.

## 3. Unusual Spending Detection
- **Service:** `backend/app/services/anomaly_service.py`
- **Endpoint:** `GET /api/analytics/anomalies`
- **Guards Against False Alerts:**
  - Requires at least 5 transactions across at least 3 distinct days before generating any alerts.
- **Checks:**
  - **Daily Category Spike:** Flags if today's spending in a category is `>= 1.8×` the user's historical daily average for that category (and `>= ₹200`).
  - **Weekly Category Surge:** Flags if the last 7 days' category spending is `>= 25%` higher than the prior weekly average (and difference `>= ₹200`).
  - **Large Single Transaction:** Flags recent transactions `>= 2.5×` the category average (and `>= ₹500`).
- **Dismissal:** Each anomaly has a deterministic `id` stored in `sessionStorage` when dismissed so it does not reappear on refresh.

## 4. Monthly Spending Forecast
- **Service:** `backend/app/services/forecast_service.py`
- **Endpoint:** `GET /api/analytics/forecast?month=YYYY-MM`
- **How it works:**
  - Computes `average_daily_spending = current_spending / days_elapsed`.
  - When prior month data is available and fewer than 20 days have elapsed, blends the current run-rate with the prior month's daily pace.
  - Generates a day-by-day `projected_series` (`actual_cumulative` vs `projected_cumulative`) rendered as **Chart D** in the Analytics view.
  - Always sets `is_estimate = True` and reports `confidence_level` (`insufficient_data`, `low`, `moderate`, or `high`).

## 5. Personalized Financial Insights
- **Service:** `backend/app/services/insights_service.py`
- **Endpoint:** `GET /api/analytics/insights?month=YYYY-MM`
- **Observations Generated:**
  - Month-over-Month overall spending change (`+X%` or `-X%`).
  - Significant category-level increases/decreases (`>= 15%`) and new categories.
  - Dominant spending category (`>= 30%` of monthly spending).
  - Peak spending day of the week.
  - Budget warnings/exceeded alerts, savings goal momentum, and forecast-vs-budget pace alerts.
