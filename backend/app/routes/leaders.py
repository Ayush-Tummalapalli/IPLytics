"""
IPLytics — Leaderboards & Stats API Routes
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.analytics.leaders_analytics import get_ipl_leaders

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics/leaders", tags=["Analytics"])

@router.get("")
def read_leaders(db: Session = Depends(get_db)) -> dict:
    """
    Get season-wise caps and Top 10 leaderboards dynamically calculated from the database.
    """
    logger.info("API request: fetch dynamic IPL leaderboards")
    return get_ipl_leaders(db)
