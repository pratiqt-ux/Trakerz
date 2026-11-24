"""
FastAPI Main Application for Trakerz Milestone 4.
Sets up middleware, API routes, and serves the modernized desktop/mobile web application.
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.config import settings
from app.routes.expenses import router as expenses_router
from app.routes.budgets import router as budgets_router
from app.routes.savings import router as savings_router
from app.routes.analytics import router as analytics_router
from app.routes.ai import router as ai_router

# Initialize FastAPI
app = FastAPI(
    title="Trakerz AI Financial Suite API",
    description="Milestone 5: AI Financial Intelligence & Smart Spending Assistant",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS so browser clients can connect from any network interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(expenses_router)
app.include_router(budgets_router)
app.include_router(savings_router)
app.include_router(analytics_router)
app.include_router(ai_router)

# Mount mobile/web client directory
mobile_dir = settings.MOBILE_DIR
if mobile_dir.exists():
    app.mount("/static", StaticFiles(directory=str(mobile_dir)), name="mobile_static")

    @app.get("/", include_in_schema=False)
    def serve_mobile_home():
        """Serve modernized finance dashboard at root."""
        index_file = mobile_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Trakerz API Running. Frontend index.html not found."}

    @app.get("/manifest.json", include_in_schema=False)
    def serve_manifest():
        manifest_file = mobile_dir / "manifest.json"
        if manifest_file.exists():
            return FileResponse(manifest_file, media_type="application/manifest+json")
        return {"error": "Manifest not found"}

    @app.get("/service-worker.js", include_in_schema=False)
    def serve_sw():
        sw_file = mobile_dir / "service-worker.js"
        if sw_file.exists():
            return FileResponse(sw_file, media_type="application/javascript")
        return {"error": "Service worker not found"}
else:
    @app.get("/", include_in_schema=False)
    def serve_root():
        return RedirectResponse(url="/docs")
