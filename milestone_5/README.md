# Trakerz — Milestone 5: AI Financial Intelligence & Smart Spending Assistant

Welcome to **Trakerz Milestone 5**, an AI-powered personal financial intelligence application built as an independent upgrade over Milestone 4.

---

## What Milestone 5 Adds

1. **AI Financial Chat Assistant (`/api/ai/chat`)**
   - Modern conversational interface integrated into Trakerz.
   - Answers questions using your **actual** Trakerz expenses, budgets, savings goals, forecasts, and insights.
   - Powered by **Google Gemini (`gemini-2.5-flash`)** via secure backend REST API calls.
   - Graceful error handling when `GEMINI_API_KEY` is missing, invalid, rate-limited, or offline—never fakes AI responses.
2. **Smart Expense Categorization (`/api/ai/categorize`)**
   - Automatically suggests categories (e.g., `"Dominos pizza 450"` &rarr; `Food`, `"Uber ride to college 180"` &rarr; `Travel`) and cleans descriptions.
   - Prefers existing user categories to prevent duplicates, with full manual override.
   - Works offline via deterministic keyword rules and optionally refines via Gemini AI.
3. **Unusual Spending Detection (`/api/analytics/anomalies`)**
   - Flags daily category spikes (e.g., `2.1×` usual daily spending), weekly category surges, and unusually large transactions.
   - Requires minimum historical data before flagging to avoid false positives, and supports dismissing alerts.
4. **Monthly Spending Forecast (`/api/analytics/forecast`)**
   - Estimates month-end spending based on current daily run-rate and prior-month pace.
   - Displays estimated total, daily average, elapsed/remaining days, and a cumulative trajectory chart.
   - Clearly labeled as an estimate.
5. **Personalized Financial Insights (`/api/analytics/insights`)**
   - Deterministic rule-based insights grounded in real numbers (MoM shifts, top categories, budget pace, savings momentum).

---

## Quick Start (Windows / PowerShell)

1. Navigate to the Milestone 5 backend directory:
   ```powershell
   cd C:\Trakerz\milestone_5\backend
   ```
2. (Optional) Configure your Gemini API key for AI Chat in `C:\Trakerz\milestone_5\backend\.env` (see [SETUP.md](SETUP.md)):
   ```ini
   GEMINI_API_KEY=your_actual_gemini_api_key
   ```
3. Run the server:
   ```powershell
   python run.py
   ```
4. Open **[http://localhost:8000](http://localhost:8000)** in your browser (or `http://<your-laptop-ip>:8000` on your phone).

---

## Running Tests

```powershell
python C:\Trakerz\milestone_5\tests\test_m5_features.py
python C:\Trakerz\milestone_5\tests\test_m4_features.py
python C:\Trakerz\milestone_5\tests\test_live_server.py
```

---

## Documentation Index

- **[MILESTONE_5_FEATURES.md](MILESTONE_5_FEATURES.md)** — Detailed architecture & behavior of all 5 intelligence features.
- **[SETUP.md](SETUP.md)** — Step-by-step setup guide, Gemini API key instructions, and troubleshooting.
- **[LEARNING_GUIDE.md](LEARNING_GUIDE.md)** — Beginner-friendly technical walkthrough.

---

## Known Limitations

1. **AI Chat Requires Internet & API Key:** If `GEMINI_API_KEY` is not set or the device is offline, AI Chat displays a clear configuration/connection notice while all other features (tracking, budgets, forecasts, anomalies, smart categorization, charts, savings goals) continue working locally.
2. **Forecasts Are Estimates:** Month-end projections assume spending continues at a similar pace and cannot predict unexpected one-off bills.
3. **Local Wi-Fi Scope (Local Mode):** When running locally with SQLite (`trakerz_m5.db`), mobile browser access requires both devices to be on the same Wi-Fi network.
