"""
IPLytics Backend — FastAPI Application Entry Point

WHY THIS FILE EXISTS:
    This is the starting point of the entire backend. FastAPI reads this
    file to create the web server with all API routes registered.

HOW TO RUN:
    From the project root directory:
        uvicorn backend.app.main:app --reload

    Then visit:
        http://localhost:8000/health  → health check
        http://localhost:8000/docs    → interactive API documentation
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.routes import (
    player_router,
    team_router,
    venue_router,
    comparison_router,
    ai_router,
)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# --- Create FastAPI Application ---
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered IPL Analytics Platform — REST API",
    version=settings.APP_VERSION,
)

# --- CORS Middleware ---
# Allow the Streamlit frontend (port 8501) to call the backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routers ---
app.include_router(player_router)
app.include_router(team_router)
app.include_router(venue_router)
app.include_router(comparison_router)
app.include_router(ai_router)


# --- Health Check Endpoint ---
@app.get("/health", tags=["System"])
def health_check() -> dict:
    """
    Health check endpoint.

    Returns a simple JSON response to verify the server is running.
    Useful for deployment health probes and quick manual checks.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# --- Startup Event ---
@app.on_event("startup")
def on_startup() -> None:
    """Log a message when the server starts."""
    logger.info(
        "🏏 %s v%s is starting up...",
        settings.APP_NAME,
        settings.APP_VERSION,
    )
    logger.info("📄 API docs available at http://%s:%s/docs", settings.BACKEND_HOST, settings.BACKEND_PORT)
    logger.info("📡 Registered routes: /players, /teams, /venues, /compare, /ai")


