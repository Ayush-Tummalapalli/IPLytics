"""
IPLytics — Team API Routes

Endpoints:
    GET /teams          → List all teams (with optional search)
    GET /teams/{name}   → Get detailed stats for a specific team
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.analytics.team_analytics import (
    get_all_teams,
    get_team_stats,
    get_team_season_performance,
    search_teams,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("")
def list_teams(
    search: str | None = Query(None, description="Search teams by name or abbreviation"),
    db: Session = Depends(get_db),
) -> dict:
    """
    List all teams or search by name/abbreviation.

    - Without `search`: returns all 16 teams
    - With `search=MI`: returns matching teams
    """
    if search:
        teams = search_teams(db, search)
    else:
        teams = get_all_teams(db)

    return {"count": len(teams), "teams": teams}


@router.get("/{name}")
def get_team(
    name: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get comprehensive statistics for a team.

    Returns overall stats and season-wise performance.

    Example: GET /teams/Mumbai Indians
    """
    logger.info("API request: team stats for '%s'", name)

    stats = get_team_stats(db, name)

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{name}' not found.",
        )

    season_performance = get_team_season_performance(db, name)

    return {
        "stats": stats,
        "season_performance": season_performance,
    }
