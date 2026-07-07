"""
IPLytics — Leaderboards & Stats API Routes
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.analytics.leaders_analytics import get_ipl_leaders, get_season_champions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics/leaders", tags=["Analytics"])

@router.get("")
def read_leaders(db: Session = Depends(get_db)) -> dict:
    """
    Get season-wise caps and Top 10 leaderboards dynamically calculated from the database.
    """
    logger.info("API request: fetch dynamic IPL leaderboards")
    return get_ipl_leaders(db)


@router.get("/champions")
def read_champions(db: Session = Depends(get_db)) -> list[dict]:
    """
    Get the list of IPL champions for each season from 2008 to 2025.
    """
    logger.info("API request: fetch dynamic IPL champions timeline")
    return get_season_champions(db)
