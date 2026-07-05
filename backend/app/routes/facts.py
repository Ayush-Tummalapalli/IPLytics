"""
IPLytics — Trivia & Facts API Routes
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.analytics.facts_analytics import get_ipl_facts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics/facts", tags=["Analytics"])

@router.get("")
def read_facts(db: Session = Depends(get_db)) -> dict:
    """
    Get 25 interesting IPL facts dynamically calculated from the database.
    """
    logger.info("API request: fetch dynamic IPL facts")
    return get_ipl_facts(db)
