"""
Configuration module for Trakerz Milestone 3.
Loads settings from environment variables or .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Path references
BACKEND_DIR = Path(__file__).resolve().parent.parent
M3_ROOT = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


class Settings:
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Storage Mode: "sqlite" or "firestore"
    STORAGE_MODE: str = os.getenv("STORAGE_MODE", "sqlite").lower()

    # SQLite Settings (kept strictly inside milestone_3)
    SQLITE_DB_NAME: str = os.getenv("SQLITE_DB_PATH", "trakerz_m3.db")
    SQLITE_PATH: Path = BACKEND_DIR / SQLITE_DB_NAME

    # Cloud Firestore Settings
    _raw_creds: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip("\"'")
    if _raw_creds:
        _p = Path(_raw_creds)
        if not _p.is_absolute() or not _p.exists():
            # If not absolute or if backslashes got escaped by dotenv, check in BACKEND_DIR
            _candidate = BACKEND_DIR / _p.name
            if _candidate.exists():
                _p = _candidate
        GOOGLE_APPLICATION_CREDENTIALS: str = str(_p)
    else:
        GOOGLE_APPLICATION_CREDENTIALS: str = ""

    FIRESTORE_PROJECT_ID: str = os.getenv("FIRESTORE_PROJECT_ID", "").strip("\"'")
    FIRESTORE_COLLECTION: str = os.getenv("FIRESTORE_COLLECTION", "expenses").strip("\"'")

    # Mobile static directory
    MOBILE_DIR: Path = M3_ROOT / "mobile"


settings = Settings()
