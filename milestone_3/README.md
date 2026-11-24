# Trakerz — Milestone 3: Mobile Accessibility & Cloud Expense Management

Welcome to **Trakerz Milestone 3**! This milestone transforms Trakerz from a laptop-bound desktop software into a **cross-platform, mobile-first web application** backed by a high-performance **Python FastAPI** REST API and a dual-mode storage engine (**Local SQLite** and **Cloud Google Firestore**).

---

## 1. Project Background & Evolution

| Milestone | Platform | Storage | Limitation Solved | Remaining Problem |
| :--- | :--- | :--- | :--- | :--- |
| **Milestone 1** | Terminal CLI (`Expense_Tracker.py`) | In-memory Python list | Initial prototype | All expense data disappeared when CLI closed. |
| **Milestone 2** | Desktop GUI (`Tkinter` + SQLite) | Local SQLite DB (`trakerz.db`) | Data loss solved with persistent storage | Bound to the laptop. Impossible to record expenses on the go. |
| **Milestone 3** | **Mobile Web PWA + FastAPI** | **SQLite (Local) & Firestore (Cloud)** | **Real-time access anywhere on smartphones and multiple devices.** | Production internet deployment requires public hosting (e.g. Render/Railway). |

---

## 2. The Problem Solved in Milestone 3

In daily life, expenses occur on the go (at canteens, tea stalls, bus stands, and grocery stores). Carrying a laptop everywhere to record an expense is impractical.

**Milestone 3 solves this by:**
1. Providing a **responsive, touch-friendly mobile interface** accessible from Android phone browsers.
2. Enabling **home-screen installation** via Progressive Web App (PWA) standards (service worker, manifest, touch icons).
3. Implementing a clean **database abstraction** that functions out-of-the-box locally with SQLite and seamlessly switches to **Google Cloud Firestore** for cloud storage across devices.

---

## 3. Technology Stack & Why It Was Chosen

* **Backend: Python FastAPI**
  * *Why:* Extremely fast, asynchronous, lightweight, automatically generates interactive OpenAPI/Swagger documentation (`/docs`), and enforces strict request validation using Pydantic.
* **Frontend: Vanilla HTML5, CSS3, & Modern JavaScript (ES6+)**
  * *Why:* Zero build tools required (no heavy node_modules or Webpack build steps), instant loading on mobile browsers, and accessible to any CSE student to inspect and understand.
* **Storage: SQLite (Local) + Google Cloud Firestore (Cloud)**
  * *Why:* SQLite provides instant, zero-configuration local persistence that requires no cloud setup or internet connection. Firestore provides a secure cloud NoSQL document database accessible across devices.
* **Architecture: RESTful JSON Client-Server Architecture**
  * *Why:* Strict separation of concerns between user interface (Frontend) and business logic/data persistence (Backend).

---

## 4. Directory Structure

Milestone 3 is completely self-contained in `C:\Trakerz\milestone_3`:

```
C:\Trakerz\milestone_3\
├── backend\
│   ├── app\
│   │   ├── __init__.py           # Package marker
│   │   ├── main.py               # FastAPI application setup, static mounting, CORS
│   │   ├── config.py             # Settings and environment variable loader
│   │   ├── models\
│   │   │   ├── __init__.py
│   │   │   └── expense.py        # Pydantic schemas & validation rules
│   │   ├── database\
│   │   │   ├── __init__.py       # Database factory (SQLite vs Firestore selector)
│   │   │   ├── base.py           # Abstract BaseExpenseDatabase interface
│   │   │   ├── sqlite_db.py      # SQLite persistent storage implementation
│   │   │   └── firestore_db.py   # Cloud Firestore implementation
│   │   ├── routes\
│   │   │   ├── __init__.py
│   │   │   └── expenses.py       # REST API endpoints (CRUD + Analytics)
│   │   └── services\
│   │       ├── __init__.py
│   │       └── expense_service.py # Business logic & calculations
│   ├── .env.example              # Template for environment configuration
│   ├── requirements.txt          # Python dependencies
│   └── run.py                    # Server startup script with network IP banner
├── mobile\
│   ├── index.html                # Mobile-first single page UI
│   ├── manifest.json             # PWA manifest for home-screen install
│   ├── service-worker.js         # Offline app-shell caching
│   ├── css\
│   │   └── style.css             # Responsive styling & thumb-friendly controls
│   ├── js\
│   │   └── app.js                # Frontend client logic & API interaction
│   └── icons\
│       ├── icon-192.png          # PWA 192x192 icon
│       ├── icon-512.png          # PWA 512x512 icon
│       ├── icon.svg              # Scalable vector logo
│       └── generate_icons.py     # Standalone icon generator script
├── tests\
│   ├── test_e2e.py               # 23 automated end-to-end integration tests
│   └── test_live_server.py       # Subprocess live socket verification test
├── README.md                     # Project documentation (this file)
└── LEARNING_GUIDE.md             # Beginner guide for 1st-year CSE students
```

---

## 5. Installation & Setup (Windows / PowerShell)

### Step 1: Open PowerShell
Navigate to the Milestone 3 backend directory:
```powershell
cd C:\Trakerz\milestone_3\backend
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Server
```powershell
python run.py
```

Upon launching, the terminal displays:
```
============================================================
   TRAKERZ - MILESTONE 3: MOBILE & CLOUD EXPENSE MANAGER
============================================================
 * Mode:            SQLITE MODE
 * Local Laptop:    http://localhost:8000
 * Mobile Phone:    http://192.168.x.x:8000
 * API Docs:        http://localhost:8000/docs
============================================================
```

Open `http://localhost:8000` in your laptop browser to see the mobile app interface immediately!

---

## 6. Accessing Trakerz From Your Android Phone

To access Trakerz on your smartphone over your local Wi-Fi network:

1. **Ensure Both Devices are on the Same Wi-Fi:**
   Connect both your laptop and Android smartphone to the same Wi-Fi router or mobile hotspot.
2. **Find Your Laptop's Local IP Address:**
   Run `ipconfig` in PowerShell:
   ```powershell
   ipconfig
   ```
   Look for **IPv4 Address** under your active Wi-Fi adapter (e.g. `192.168.1.15`).
3. **Open Chrome on Your Android Phone:**
   Navigate to:
   ```
   http://<your-laptop-ip>:8000
   ```
   *(Example: `http://192.168.1.15:8000`)*
4. **Install as a Mobile App (PWA):**
   * Tap the three dots menu (**⋮**) in Chrome.
   * Tap **"Add to Home screen"** or **"Install app"**.
   * An icon titled **Trakerz** will appear on your phone's home screen! Tapping it opens Trakerz full-screen without address bar clutter.

> [!NOTE]
> If your phone cannot connect, verify that **Windows Defender Firewall** is allowing Python to accept incoming connections on private networks. You can run:
> `New-NetFirewallRule -DisplayName "Trakerz Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow`

---

## 7. Cloud Storage Integration (Google Cloud Firestore)

Trakerz has a built-in database abstraction that supports both **Local SQLite** and **Google Cloud Firestore**.

### How to Enable Cloud Firestore:

1. Create a project in the [Firebase Console](https://console.firebase.google.com/).
2. In the sidebar, navigate to **Firestore Database** and click **Create Database** (start in Test Mode or configure security rules).
3. Go to **Project Settings (gear icon) &rarr; Service Accounts &rarr; Generate New Private Key**.
4. Save the downloaded JSON file securely (e.g. `C:\Trakerz\milestone_3\backend\serviceAccountKey.json`).
   > [!CAUTION]
   > Never commit your service account JSON file to GitHub or share it publicly!
5. In `C:\Trakerz\milestone_3\backend`, copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```
6. Edit `.env` and set:
   ```ini
   STORAGE_MODE=firestore
   GOOGLE_APPLICATION_CREDENTIALS=C:\Trakerz\milestone_3\backend\serviceAccountKey.json
   FIRESTORE_PROJECT_ID=your-firebase-project-id
   FIRESTORE_COLLECTION=expenses
   ```
7. Start the server: `python run.py`. The status badge in the app will turn blue: `☁️ Cloud Firestore`.

*(If credentials are not supplied or invalid, the backend automatically and safely falls back to Local SQLite mode).*

---

## 8. REST API Endpoints

All endpoints accept and return JSON. Interactive documentation is available at `http://localhost:8000/docs`.

### Expense Endpoints

| Method | Endpoint | Description | Request Body Example | Status Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/expenses` | List all expenses | None | `200 OK` |
| `POST` | `/api/expenses` | Create new expense | `{"category": "Food", "amount": 150.0, "date": "2026-11-24", "description": "Dinner"}` | `201 Created` |
| `GET` | `/api/expenses/{id}` | Get single expense | None | `200 OK` |
| `PUT` | `/api/expenses/{id}` | Update expense | `{"amount": 180.0, "description": "Dinner + drink"}` | `200 OK` |
| `DELETE` | `/api/expenses/{id}` | Delete expense | None | `200 OK` |

### Analytics & System Endpoints

| Method | Endpoint | Description | Response Example |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | System health check | `{"status": "healthy", "mode": "local", "database": "sqlite"}` |
| `GET` | `/api/status` | Detailed storage status | `{"mode": "local", "database": "sqlite", "cloud_configured": false}` |
| `GET` | `/api/analytics/total` | Total spend & monthly total | `{"total_amount": 1250.0, "expense_count": 5, "current_month_total": 850.0}` |
| `GET` | `/api/analytics/categories` | Spending by category | `[{"category": "Food", "total": 600.0, "percentage": 48.0, "count": 3}]` |
| `GET` | `/api/analytics/monthly` | Month-by-month spending | `[{"month": "2026-11", "total": 850.0, "count": 4, "is_current_month": true}]` |

---

## 9. Automated Testing & Verification

Milestone 3 includes a 23-step automated test suite that validates validation rules, CRUD operations, analytics computations, static file serving, and data persistence.

Run the tests at any time:
```powershell
python C:\Trakerz\milestone_3\tests\test_e2e.py
```

Expected result:
```
============================================================
RUNNING TRAKERZ MILESTONE 3 AUTOMATED TEST SUITE
============================================================
 [PASS] 1. Health Endpoint Check
 [PASS] 2. System Status Endpoint (Local Mode)
 [PASS] 3. Reject Negative Amount (Status 422)
 [PASS] 4. Reject Zero Amount (Status 422)
 [PASS] 5. Reject Empty Category (Status 422)
 [PASS] 6. Reject Invalid Date (Status 422)
 [PASS] 7. Add Valid Expense #1 (Food, ₹250.50)
 [PASS] 8. Add Valid Expense #2 (Travel, ₹120.00)
 [PASS] 9. Retrieve Single Expense by ID
 [PASS] 10. List All Expenses (Count = 2)
 [PASS] 11. Total Analytics Sum (Expected: 370.50, Got: 370.5)
 [PASS] 12. Category Breakdown Analytics
 [PASS] 13. Monthly Summary Analytics
 [PASS] 14. Update Expense Amount & Description
 [PASS] 15. Analytics Reflects Updated Amount (₹400.50)
 [PASS] 16. Delete Expense by ID
 [PASS] 17. Non-Existent Expense Returns 404
 [PASS] 18. Database State After Deletion
 [PASS] 19. Mobile App Index HTML Served at Root
 [PASS] 20. Mobile CSS Served
 [PASS] 21. Mobile JavaScript Served
 [PASS] 22. PWA Manifest & Service Worker Served
 [PASS] 23. Data Persistence Across Database Reconnect
============================================================
TEST RESULTS: 23 PASSED, 0 FAILED
============================================================
```

---

## 10. Known Limitations & Future Improvements

### Current Limitations:
1. **Local Wi-Fi Bound (when in Local SQLite Mode):** When running locally, your smartphone must be connected to the same Wi-Fi network as the host laptop.
2. **Single-User Scope:** Trakerz is currently configured for a single user without multi-user password authentication or sessions.
3. **Offline Sync:** The service worker caches the mobile application shell so it opens instantly offline, but recording expenses while completely offline requires a local IndexedDB sync queue (which is marked for future implementation).

### Future Roadmap:
* Multi-user authentication (OAuth with Google / Firebase Auth).
* Offline queue using IndexedDB + BackgroundSync API.
* Export expense reports to CSV/PDF.
* Spending budget limits with alert notifications.
