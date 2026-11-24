# Trakerz — Milestone 4: Enhanced GUI & Smart Financial Insights

Welcome to **Trakerz Milestone 4**! This milestone elevates Trakerz from a mobile expense recorder into a **complete modern personal fintech application**, featuring:

* 🎨 **Redesigned Modern GUI:** Polished dark slate/navy fintech aesthetic, desktop sidebar, and thumb-friendly mobile bottom navigation.
* 🎯 **Monthly Category Budgets:** Set spending limits with visual progress bars and dynamic **80% (Warning)** and **100% (Exceeded)** alerts.
* 📈 **Interactive Chart.js Visualizations:** Category doughnut breakdown, monthly spending trend line chart, and daily bar chart.
* 💡 **Smart Financial Insights:** Deterministic Month-over-Month (MoM) comparisons, category shifts, and peak spending day detection.
* 💰 **Savings Goals & Contribution Tracking:** Goal progress tracking, deposit logging, and automatic completion detection.
* 🔒 **Complete Milestone Isolation:** Milestone 4 operates with its own isolated database (`trakerz_m4.db`) without modifying Milestones 1, 2, or 3.

---

## 1. Project Evolution: Milestone 1 &rarr; 2 &rarr; 3 &rarr; 4

| Milestone | Platform | Storage | Core Feature | New Limitation Solved |
| :--- | :--- | :--- | :--- | :--- |
| **Milestone 1** | CLI (`Expense_Tracker.py`) | In-memory List | Basic expense entry | Initial prototype. Data lost on close. |
| **Milestone 2** | Desktop GUI (Tkinter) | Local SQLite (`trakerz.db`) | Local persistence | Data loss solved, but restricted to laptop. |
| **Milestone 3** | Mobile Web PWA + FastAPI | Dual Engine (SQLite / Firestore) | Mobile browser access | Accessible anywhere on smartphones via Wi-Fi/Cloud. |
| **Milestone 4** | **Modern Fintech Suite** | **Isolated SQLite (`trakerz_m4.db`)** | **Budgets, Alerts, Charts, Insights & Savings** | **Visual design overhaul & proactive financial planning.** |

---

## 2. Directory Structure

Milestone 4 is completely isolated inside `C:\Trakerz\milestone_4`:

```
C:\Trakerz\milestone_4\
├── backend\
│   ├── app\
│   │   ├── __init__.py           # Package initialization
│   │   ├── config.py             # Settings (points to trakerz_m4.db)
│   │   ├── main.py               # FastAPI entry point, CORS, routers
│   │   ├── database\
│   │   │   ├── __init__.py       # Database factory
│   │   │   ├── base.py           # Abstract BaseExpenseDatabase interface
│   │   │   ├── sqlite_db.py      # SQLite implementation (expenses, budgets, savings)
│   │   │   └── firestore_db.py   # Cloud Firestore implementation
│   │   ├── models\
│   │   │   ├── __init__.py
│   │   │   ├── expense.py        # Expense schemas
│   │   │   ├── budget.py         # Category budget & alert schemas
│   │   │   ├── savings.py        # Savings goals & contribution schemas
│   │   │   └── insights.py       # Chart points & MoM insight schemas
│   │   ├── routes\
│   │   │   ├── __init__.py
│   │   │   ├── expenses.py       # Expense CRUD endpoints
│   │   │   ├── budgets.py        # Budget & alert endpoints
│   │   │   ├── savings.py        # Savings goals & contribution endpoints
│   │   │   └── analytics.py      # Charts, dashboard overview & MoM insights
│   │   └── services\
│   │       ├── __init__.py
│   │       ├── expense_service.py # Business logic for expenses
│   │       ├── budget_service.py  # Budget calculation & alerts
│   │       ├── savings_service.py # Savings goal calculations
│   │       └── insights_service.py # MoM comparisons & chart aggregations
│   ├── .env                      # Milestone 4 environment configuration
│   ├── .env.example              # Template
│   ├── requirements.txt          # Python dependencies
│   ├── run.py                    # Server launcher
│   └── trakerz_m4.db             # Independent SQLite database
├── mobile\
│   ├── index.html                # Modern single-page fintech dashboard
│   ├── manifest.json             # PWA manifest
│   ├── service-worker.js         # Offline shell caching (v4)
│   ├── css\
│   │   └── style.css             # Fintech dark theme, desktop sidebar & mobile nav
│   ├── js\
│   │   ├── app.js                # Frontend client logic & chart integrations
│   │   └── vendor\
│   │       └── chart.umd.min.js  # Locally bundled Chart.js (offline ready)
│   └── icons\
│       ├── icon-192.png
│       ├── icon-512.png
│       └── icon.svg
├── tests\
│   ├── test_e2e.py               # Baseline regression test suite
│   ├── test_m4_features.py       # 29 automated tests for Milestone 4 features
│   └── test_live_server.py       # Live socket verification script
├── README.md                     # Technical documentation (this file)
└── LEARNING_GUIDE.md             # Beginner learning guide for 1st-year CSE students
```

---

## 3. New Features in Milestone 4

### A. Modern Fintech GUI
* **Desktop Sidebar:** Fixed navigation bar with SVG icons, quick links, active indicator, and live storage status.
* **Mobile Bottom Bar:** Ergonomic bottom tab navigation optimized for single-hand smartphone use.
* **KPI Header Cards:** Displays Total Spending This Month, Spending Today, Remaining Monthly Budget, and Total Transactions.
* **Global Month Selector:** Filter the entire dashboard, budgets, and analytics by any month (`YYYY-MM`).

### B. Monthly Category Budgets & Alerts
* Define allocated spending limits per category per month (e.g., Food: ₹4,000, Travel: ₹1,500).
* Visual progress bar dynamically changes color:
  * 🟢 **Normal (<80%):** On track.
  * 🟡 **Warning (80% - 99%):** Warning banner triggered.
  * 🔴 **Exceeded (>=100%):** Exceeded banner showing exact overspent amount (`+₹... over limit`).
* Dismissable alert banners prevent repeated annoying popups across session tabs.

### C. Smart Interactive Charts (Chart.js)
* **Chart A (Category Spending):** Interactive doughnut chart showing percentage distribution across categories with custom tooltips.
* **Chart B (Monthly Trend):** Line chart with smooth cubic interpolation tracking spending over time.
* **Chart C (Daily Spending):** Day-by-day bar chart of the selected month with the current day highlighted in emerald green.
* **100% Offline Ready:** Chart.js is bundled locally inside `mobile/js/vendor/chart.umd.min.js`.

### D. Month-over-Month (MoM) Financial Insights
* Algorithmic comparisons between current and previous month:
  * Overall percentage increase or decrease.
  * Category shifts (e.g., "Food spending increased 18% compared to last month").
  * Dominant category detection (categories taking >30% of monthly budget).
  * Peak spending day of the week (e.g. "Highest spending day was Sunday").

### E. Savings Goals & Contributions
* Create targeted goals with deadlines (e.g., "Laptop Fund" target ₹60,000).
* Add deposits/contributions towards a goal.
* Automatically computes saved amount, remaining amount, and percentage progress.
* Automatically marks goals as completed when target is met.

---

## 4. REST API Endpoints

### Budgets (`/api/budgets`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/budgets?month=YYYY-MM` | List budgets with spent/remaining calculations |
| `POST` | `/api/budgets` | Set or update a category budget |
| `GET` | `/api/budgets/alerts?month=YYYY-MM` | Get active 80% and 100% alerts |
| `PUT` | `/api/budgets/{id}` | Update budget limit |
| `DELETE` | `/api/budgets/{id}` | Delete a budget |

### Savings Goals (`/api/savings-goals`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/savings-goals` | List all goals with progress and contributions |
| `POST` | `/api/savings-goals` | Create a new savings goal |
| `GET` | `/api/savings-goals/{id}` | Get single goal with deposit history |
| `PUT` | `/api/savings-goals/{id}` | Update goal details or mark completed |
| `DELETE` | `/api/savings-goals/{id}` | Delete goal |
| `POST` | `/api/savings-goals/{id}/contribute` | Add deposit/contribution to a goal |

### Smart Analytics & Charts (`/api/analytics`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/analytics/dashboard-overview` | Comprehensive KPI overview for home screen |
| `GET` | `/api/analytics/daily?month=YYYY-MM` | Daily spending data for Chart C |
| `GET` | `/api/analytics/monthly-trend` | Monthly spending history for Chart B |
| `GET` | `/api/analytics/category-month` | Category breakdown for Chart A |
| `GET` | `/api/analytics/insights?month=YYYY-MM` | Algorithmic MoM financial insights |

---

## 5. Installation & Run Instructions (Windows / PowerShell)

```powershell
cd C:\Trakerz\milestone_4\backend
python run.py
```

The terminal will print:
```
=================================================================
   TRAKERZ - MILESTONE 4: ENHANCED GUI & SMART FINANCIAL INSIGHTS
=================================================================
 * Mode:            SQLITE MODE
 * Local Laptop:    http://localhost:8000
 * Mobile Phone:    http://192.168.x.x:8000
 * API Docs:        http://localhost:8000/docs
=================================================================
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 6. Automated Testing

Milestone 4 includes a 29-step automated test suite:

```powershell
python C:\Trakerz\milestone_4\tests\test_m4_features.py
```

Results:
```
=================================================================
TRAKERZ MILESTONE 4: FULL FEATURE & REGRESSION TEST SUITE
=================================================================

--- 1. Expenses & Validation ---
 [PASS] 1.1 Reject invalid expense payload
 [PASS] 1.2 Add valid Food expense (₹400.00)
 [PASS] 1.3 Add valid Travel expense (₹250.00)
 [PASS] 1.4 List all expenses
 [PASS] 1.5 Total spending calculation (₹650.00)

--- 2. Category Budgets & Alert System ---
 [PASS] 2.1 Create Food budget (₹1,000 limit, 40% used -> normal)
 [PASS] 2.2 80% Budget Warning Triggered (Travel 83.3% used -> warning)
 [PASS] 2.3 Budget Warning Alert returned in /api/budgets/alerts
 [PASS] 2.4 Added ₹700 to Food
 [PASS] 2.5 100% Budget Exceeded Triggered (Food spent ₹1,100 of ₹1,000 -> overspent ₹100.00)
 [PASS] 2.6 Edit Budget Limit to ₹2,000 (status returns to normal)
 [PASS] 2.7 Delete Travel budget

--- 3. Savings Goals & Contributions ---
 [PASS] 3.1 Create Savings Goal (Target: ₹50,000.00)
 [PASS] 3.2 Add Contribution #1 (₹20,000.00)
 [PASS] 3.3 Goal Progress Calculation (₹20,000 saved, ₹30,000 remaining, 40% progress)
 [PASS] 3.4 Add Contribution #2 (₹30,000.00)
 [PASS] 3.5 Auto-mark Goal Completed (100% reached)
 [PASS] 3.6 Edit Savings Goal details

--- 4. Chart.js Analytics Endpoints ---
 [PASS] 4.1 Chart A: Category Spending breakdown returned
 [PASS] 4.2 Chart B: Monthly Trend history returned
 [PASS] 4.3 Chart C: Daily spending breakdown for all days returned

--- 5. Month-over-Month (MoM) Financial Insights ---
 [PASS] 5.1 MoM algorithmic insights generated successfully
 [PASS] 5.2 Dashboard Overview endpoint returned aggregated KPIs

--- 6. Static Assets & Vendor Bundle ---
 [PASS] 6.1 Modernized index.html served at root
 [PASS] 6.2 Modern CSS with desktop sidebar & bottom bar served
 [PASS] 6.3 Milestone 4 JavaScript served
 [PASS] 6.4 Locally bundled Chart.js vendor script served
 [PASS] 6.5 Service worker with v4 shell caching served

--- 7. Database Persistence ---
 [PASS] 7.1 Full persistence across connection reconnect (Expenses, Budgets, Savings Goals preserved)

=================================================================
MILESTONE 4 TEST RESULTS: 29 PASSED, 0 FAILED
=================================================================
```
