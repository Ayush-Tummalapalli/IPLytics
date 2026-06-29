"""
IPLytics — Venue Analytics Service

WHY THIS FILE EXISTS:
    This module computes venue-specific analytics — average scores,
    chase success rates, and scoring patterns at each IPL ground.
    Venue analysis is crucial for understanding home advantage
    and pitch behavior.

HOW IT WORKS:
    Queries matches and deliveries tables to compute venue-level
    statistics. Joins matches with deliveries to get innings-level
    scoring data per venue.

WHERE IT FITS:
    Called by API routes, AI assistant, and frontend components
    for venue dashboards and venue-based insights.
"""

import logging

from sqlalchemy import func, case, and_, distinct
from sqlalchemy.orm import Session

from backend.app.models.delivery import Delivery
from backend.app.models.match import Match

logger = logging.getLogger(__name__)


def get_all_venues(session: Session) -> list[str]:
    """
    Get a sorted list of all unique venues.

    Returns: ["M Chinnaswamy Stadium", "Wankhede Stadium", ...]
    """
    venues = session.query(distinct(Match.venue)).order_by(Match.venue).all()
    return [v[0] for v in venues]


def get_venue_stats(session: Session, venue_name: str) -> dict:
    """
    Compute comprehensive statistics for a venue.

    Returns:
        {
            "venue": "M Chinnaswamy Stadium",
            "city": "Bangalore",
            "total_matches": 85,
            "avg_first_innings_score": 172.5,
            "avg_second_innings_score": 158.3,
            "highest_total": 263,
            "lowest_total": 82,
            "avg_score": 165.4,
            "chase_success_rate": 45.6,
            "bat_first_win_pct": 54.4,
        }
    """
    logger.info("Computing venue stats for: %s", venue_name)

    # --- Total matches at this venue ---
    total_matches = session.query(func.count(Match.id)).filter(
        Match.venue == venue_name,
    ).scalar() or 0

    if total_matches == 0:
        return {"venue": venue_name, "total_matches": 0}

    # --- City ---
    city = session.query(Match.city).filter(
        Match.venue == venue_name,
        Match.city != "Unknown",
    ).first()
    city_name = city[0] if city else "Unknown"

    # --- Innings scores (1st and 2nd innings totals per match) ---
    innings_scores = session.query(
        Delivery.match_id,
        Delivery.innings,
        func.sum(Delivery.runs_total).label("total_runs"),
    ).join(
        Match, Delivery.match_id == Match.id,
    ).filter(
        Match.venue == venue_name,
        Delivery.innings.in_([1, 2]),  # Only main innings
    ).group_by(
        Delivery.match_id, Delivery.innings,
    ).all()

    first_innings_scores = [r.total_runs for r in innings_scores if r.innings == 1]
    second_innings_scores = [r.total_runs for r in innings_scores if r.innings == 2]
    all_scores = [r.total_runs for r in innings_scores]

    avg_first = round(sum(first_innings_scores) / len(first_innings_scores), 1) if first_innings_scores else 0
    avg_second = round(sum(second_innings_scores) / len(second_innings_scores), 1) if second_innings_scores else 0
    avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    highest_total = max(all_scores) if all_scores else 0
    lowest_total = min(all_scores) if all_scores else 0

    # --- Chase success rate ---
    # Matches where team batting second won
    matches_with_result = session.query(Match).filter(
        Match.venue == venue_name,
        Match.winner_id.isnot(None),
    ).all()

    chases_won = 0
    chases_total = 0

    for match in matches_with_result:
        chases_total += 1
        # Team batting second = team2 if toss winner chose field,
        # or team1 if toss winner chose bat
        # Simpler: if winner is not the team that set the target
        # The team that bats first: if toss_decision == 'bat', toss_winner bats first
        # Otherwise toss_winner fields first (other team bats first)
        if match.toss_decision == "bat":
            batting_first_id = match.toss_winner_id
        else:
            batting_first_id = match.toss_winner_id  # fields first → other team bats first
            # Actually: if toss winner chose field, THEY field first
            # So the OTHER team bats first
            if match.toss_winner_id == match.team1_id:
                batting_first_id = match.team2_id
            else:
                batting_first_id = match.team1_id

        # For bat decision: toss winner bats first
        if match.toss_decision == "bat":
            batting_first_id = match.toss_winner_id

        # Chase won = winner is NOT the team that batted first
        if match.winner_id != batting_first_id:
            chases_won += 1

    chase_success_rate = round((chases_won / chases_total) * 100, 1) if chases_total > 0 else 0
    bat_first_win_pct = round(100 - chase_success_rate, 1)

    return {
        "venue": venue_name,
        "city": city_name,
        "total_matches": total_matches,
        "avg_first_innings_score": avg_first,
        "avg_second_innings_score": avg_second,
        "highest_total": highest_total,
        "lowest_total": lowest_total,
        "avg_score": avg_score,
        "chase_success_rate": chase_success_rate,
        "bat_first_win_pct": bat_first_win_pct,
    }


def get_venue_season_scores(session: Session, venue_name: str) -> list[dict]:
    """
    Get average scores per season at a venue.

    Returns:
        [{"season": 2023, "avg_score": 175.2, "matches": 8}, ...]
    """
    results = session.query(
        Match.season,
        func.count(distinct(Match.id)).label("matches"),
        func.avg(Delivery.runs_total).label("avg_runs_per_ball"),
    ).join(
        Delivery, Delivery.match_id == Match.id,
    ).filter(
        Match.venue == venue_name,
    ).group_by(
        Match.season,
    ).order_by(
        Match.season,
    ).all()

    # Convert avg runs per ball to approximate innings total
    # (roughly 120 legal balls per innings in T20)
    return [
        {
            "season": r.season,
            "matches": r.matches,
            "avg_runs_per_ball": round(float(r.avg_runs_per_ball), 3) if r.avg_runs_per_ball else 0,
        }
        for r in results
    ]


def search_venues(session: Session, query: str) -> list[str]:
    """
    Search venues by partial name match.
    """
    results = session.query(distinct(Match.venue)).filter(
        Match.venue.ilike(f"%{query}%")
    ).order_by(Match.venue).limit(20).all()

    return [r[0] for r in results]
