"""
IPLytics — Comparison API Routes

Endpoints:
    GET /compare/players  → Compare two players side-by-side
    GET /compare/teams    → Compare two teams (head-to-head + stats)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.analytics.player_analytics import (
    get_player_batting_stats,
    get_player_bowling_stats,
)
from backend.app.analytics.team_analytics import (
    get_team_stats,
    get_head_to_head,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compare", tags=["Comparisons"])


@router.get("/players")
def compare_players(
    player1: str = Query(..., description="First player name"),
    player2: str = Query(..., description="Second player name"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Compare two players side-by-side.

    Returns batting and bowling stats for both players.

    Example: GET /compare/players?player1=V Kohli&player2=RG Sharma
    """
    logger.info("API request: compare '%s' vs '%s'", player1, player2)

    # Get stats for player 1
    p1_batting = get_player_batting_stats(db, player1)
    if p1_batting["matches"] == 0:
        raise HTTPException(status_code=404, detail=f"Player '{player1}' not found.")

    p1_bowling = get_player_bowling_stats(db, player1)

    # Get stats for player 2
    p2_batting = get_player_batting_stats(db, player2)
    if p2_batting["matches"] == 0:
        raise HTTPException(status_code=404, detail=f"Player '{player2}' not found.")

    p2_bowling = get_player_bowling_stats(db, player2)

    return {
        "player1": {
            "batting": p1_batting,
            "bowling": p1_bowling,
        },
        "player2": {
            "batting": p2_batting,
            "bowling": p2_bowling,
        },
    }


@router.get("/teams")
def compare_teams(
    team1: str = Query(..., description="First team name"),
    team2: str = Query(..., description="Second team name"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Compare two teams with head-to-head record.

    Returns individual stats for both teams plus their H2H record.

    Example: GET /compare/teams?team1=Mumbai Indians&team2=Chennai Super Kings
    """
    logger.info("API request: compare '%s' vs '%s'", team1, team2)

    # Get stats for team 1
    t1_stats = get_team_stats(db, team1)
    if not t1_stats:
        raise HTTPException(status_code=404, detail=f"Team '{team1}' not found.")

    # Get stats for team 2
    t2_stats = get_team_stats(db, team2)
    if not t2_stats:
        raise HTTPException(status_code=404, detail=f"Team '{team2}' not found.")

    # Head-to-head
    h2h = get_head_to_head(db, team1, team2)

    return {
        "team1": t1_stats,
        "team2": t2_stats,
        "head_to_head": h2h,
    }
