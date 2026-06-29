"""
IPLytics — Player API Routes

Endpoints:
    GET /players          → List all players (with optional search)
    GET /players/{name}   → Get detailed stats for a specific player
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.analytics.player_analytics import (
    get_all_players,
    get_player_batting_stats,
    get_player_bowling_stats,
    get_player_season_runs,
    search_players,
    get_player_teams,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("")
def list_players(
    search: str | None = Query(None, description="Search players by name"),
    db: Session = Depends(get_db),
) -> dict:
    """
    List all players or search by name.

    - Without `search`: returns all 799 player names
    - With `search=kohli`: returns matching player names
    """
    if search:
        players = search_players(db, search)
    else:
        players = get_all_players(db)

    return {"count": len(players), "players": players}


@router.get("/{name}")
def get_player(
    name: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get comprehensive statistics for a player.

    Returns batting stats, bowling stats, and season-wise run trends.

    Example: GET /players/V Kohli
    """
    logger.info("API request: player stats for '%s'", name)

    # Get batting stats
    batting = get_player_batting_stats(db, name)

    if batting["matches"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Player '{name}' not found or has no match data.",
        )

    # Get bowling stats
    bowling = get_player_bowling_stats(db, name)

    # Get season-wise runs
    season_runs = get_player_season_runs(db, name)

    # Get player teams
    teams = get_player_teams(db, name)

    return {
        "batting": batting,
        "bowling": bowling,
        "season_runs": season_runs,
        "teams": teams,
    }
