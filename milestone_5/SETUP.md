# Trakerz Milestone 5 — Setup & Configuration Guide

## 1. Prerequisites
- **Python 3.10+** (verified on Python 3.14)
- Dependencies from `backend/requirements.txt`:
  ```powershell
  cd C:\Trakerz\milestone_5\backend
  pip install -r requirements.txt
  ```

## 2. Environment Configuration (`.env`)
Copy `.env.example` to `.env` inside `C:\Trakerz\milestone_5\backend\` (one is already created for you in local SQLite mode):

```ini
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Isolated Milestone 5 SQLite database
STORAGE_MODE=sqlite
SQLITE_DB_PATH=trakerz_m5.db

# AI Assistant (Google Gemini)
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
AI_TIMEOUT_SECONDS=20
```

## 3. Obtaining a Gemini API Key (For AI Chat Assistant)
1. Visit **[Google AI Studio](https://aistudio.google.com/apikey)** and sign in with your Google account.
2. Click **Create API Key**.
3. Copy the key and paste it into `C:\Trakerz\milestone_5\backend\.env` on the `GEMINI_API_KEY=` line.
4. Restart `python run.py`. The **AI Assistant** tab will show a green `Ready (gemini-2.5-flash)` badge.

> **Security Reminder:** Never hardcode your API key in JavaScript or Python files, and never commit `.env` to Git.

## 4. Running the Application
```powershell
cd C:\Trakerz\milestone_5\backend
python run.py
```
- **Desktop / Laptop:** Open `http://localhost:8000`
- **Android Phone (same Wi-Fi):** Open `http://<your-laptop-ip>:8000`
- **Interactive API Docs:** Open `http://localhost:8000/docs`
