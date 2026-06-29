"""
IPLytics Backend — API Route Definitions.

All routers are imported here for clean registration in main.py:
    from backend.app.routes import player_router, team_router, ...
"""

from backend.app.routes.players import router as player_router
from backend.app.routes.teams import router as team_router
from backend.app.routes.venues import router as venue_router
from backend.app.routes.comparisons import router as comparison_router
from backend.app.routes.ai import router as ai_router

__all__ = ["player_router", "team_router", "venue_router", "comparison_router", "ai_router"]

