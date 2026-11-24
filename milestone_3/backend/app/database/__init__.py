"""
Database Factory and Dependency Provider.
Instantiates either SQLiteExpenseDatabase or FirestoreExpenseDatabase
based on environment configuration.
"""
import logging
from app.config import settings
from app.database.base import BaseExpenseDatabase
from app.database.sqlite_db import SQLiteExpenseDatabase

logger = logging.getLogger("trakerz")

_db_instance: BaseExpenseDatabase = None


def get_db() -> BaseExpenseDatabase:
    """Singleton provider for active database engine."""
    global _db_instance
    if _db_instance is not None:
        return _db_instance

    mode = settings.STORAGE_MODE.lower()

    if mode == "firestore":
        try:
            from app.database.firestore_db import FirestoreExpenseDatabase
            logger.info("Initializing Cloud Firestore database backend...")
            _db_instance = FirestoreExpenseDatabase(
                credentials_path=settings.GOOGLE_APPLICATION_CREDENTIALS,
                project_id=settings.FIRESTORE_PROJECT_ID,
                collection_name=settings.FIRESTORE_COLLECTION
            )
            logger.info("Successfully connected to Cloud Firestore.")
            return _db_instance
        except Exception as e:
            logger.warning(
                f"Could not initialize Cloud Firestore ({str(e)}). "
                "Falling back safely to Local SQLite Mode."
            )
            # Safe local fallback so the app continues working reliably
            _db_instance = SQLiteExpenseDatabase(db_path=settings.SQLITE_PATH)
            return _db_instance
    else:
        logger.info(f"Using Local SQLite Database at: {settings.SQLITE_PATH}")
        _db_instance = SQLiteExpenseDatabase(db_path=settings.SQLITE_PATH)
        return _db_instance
