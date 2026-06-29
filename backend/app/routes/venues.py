"""
IPLytics — Venue API Routes

Endpoints:
    GET /venues          → List all venues (with optional search)
    GET /venues/{name}   → Get detailed stats for a specific venue
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.analytics.venue_analytics import (
    get_all_venues,
    get_venue_stats,
    get_venue_season_scores,
    search_venues,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/venues", tags=["Venues"])


@router.get("")
def list_venues(
    search: str | None = Query(None, description="Search venues by name"),
    db: Session = Depends(get_db),
) -> dict:
    """
    List all venues or search by name.

    - Without `search`: returns all 59 venues
    - With `search=wankhede`: returns matching venues
    """
    if search:
        venues = search_venues(db, search)
    else:
        venues = get_all_venues(db)

    return {"count": len(venues), "venues": venues}


@router.get("/{name:path}")
def get_venue(
    name: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get comprehensive statistics for a venue.

    Returns overall stats and season-wise scoring trends.

    Example: GET /venues/M Chinnaswamy Stadium

    Note: Uses {name:path} to allow venue names with special characters.
    """
    logger.info("API request: venue stats for '%s'", name)

    stats = get_venue_stats(db, name)

    if stats.get("total_matches", 0) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Venue '{name}' not found or has no match data.",
        )

    season_scores = get_venue_season_scores(db, name)

    return {
        "stats": stats,
        "season_scores": season_scores,
    }
