"""
Trakerz Milestone 4 - Application Entry Point
Starts the FastAPI server with Uvicorn.
"""
import os
import sys
from pathlib import Path

# Ensure backend directory is in Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from app.config import settings

def print_banner():
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

    print("=" * 65)
    print("   TRAKERZ - MILESTONE 4: ENHANCED GUI & SMART FINANCIAL INSIGHTS")
    print("=" * 65)
    print(f" * Mode:            {settings.STORAGE_MODE.upper()} MODE")
    print(f" * Local Laptop:    http://localhost:{settings.PORT}")
    print(f" * Mobile Phone:    http://{local_ip}:{settings.PORT}")
    print(f" * API Docs:        http://localhost:{settings.PORT}/docs")
    print("=" * 65)
    print(" Press CTRL+C to quit server.")
    print("=" * 65)

if __name__ == "__main__":
    print_banner()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
