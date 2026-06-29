"""
IPLytics — Player Analytics Service

WHY THIS FILE EXISTS:
    This module contains all the analytics functions for individual
    players. It computes batting and bowling statistics by querying
    the deliveries and matches tables.

HOW IT WORKS:
    Each function takes a SQLAlchemy session and player name, runs
    SQL queries via SQLAlchemy, and returns computed statistics as
    dictionaries. The functions are designed to be:
    1. Reusable — called by API routes AND the AI assistant
    2. Efficient — uses SQL aggregation instead of loading all rows
    3. Complete — returns all stats needed for the frontend

WHERE IT FITS:
    Called by:
    - API routes (Phase 5): GET /players/{name}
    - AI assistant (Phase 8): to answer player questions
    - Frontend (Phase 6): to display player dashboards
"""

import logging

from sqlalchemy import func, case, and_, distinct
from sqlalchemy.orm import Session

from backend.app.models.delivery import Delivery
from backend.app.models.match import Match
from backend.app.models.team import Team

logger = logging.getLogger(__name__)


def get_all_players(session: Session) -> list[str]:
    """
    Get a sorted list of all player names in the database.

    Used for search/autocomplete on the frontend.
    """
    from backend.app.models.player import Player

    players = session.query(Player.name).order_by(Player.name).all()
    return [p[0] for p in players]


def get_player_batting_stats(session: Session, player_name: str) -> dict:
    """
    Compute comprehensive batting statistics for a player.

    Returns:
        {
            "name": "V Kohli",
            "matches": 237,
            "innings": 225,
            "total_runs": 7263,
            "balls_faced": 5430,
            "average": 37.44,
            "strike_rate": 133.76,
            "highest_score": 113,
            "fifties": 50,
            "hundreds": 8,
            "fours": 680,
            "sixes": 250,
            "not_outs": 43,
            "ducks": 12,
        }
    """
    logger.info("Computing batting stats for: %s", player_name)

    # --- Total runs, balls faced, fours, sixes ---
    batting_agg = session.query(
        func.sum(Delivery.runs_batter).label("total_runs"),
        func.count(Delivery.id).label("balls_faced"),
        func.sum(case((Delivery.runs_batter == 4, 1), else_=0)).label("fours"),
        func.sum(case((Delivery.runs_batter == 6, 1), else_=0)).label("sixes"),
    ).filter(
        Delivery.batter == player_name,
        # Don't count wides as balls faced (batter didn't face them)
        Delivery.extra_type.is_(None) | (Delivery.extra_type != "wides"),
    ).first()

    total_runs = batting_agg.total_runs or 0
    balls_faced = batting_agg.balls_faced or 0
    fours = batting_agg.fours or 0
    sixes = batting_agg.sixes or 0

    # --- Innings-level stats (for average, 50s, 100s, highest) ---
    # An "innings" is a unique (match_id, innings) combination
    innings_runs = session.query(
        Delivery.match_id,
        Delivery.innings,
        func.sum(Delivery.runs_batter).label("runs"),
    ).filter(
        Delivery.batter == player_name,
    ).group_by(
        Delivery.match_id, Delivery.innings,
    ).all()

    innings_count = len(innings_runs)
    runs_per_innings = [row.runs for row in innings_runs]

    highest_score = max(runs_per_innings) if runs_per_innings else 0
    fifties = sum(1 for r in runs_per_innings if 50 <= r < 100)
    hundreds = sum(1 for r in runs_per_innings if r >= 100)
    ducks = sum(1 for r in runs_per_innings if r == 0)

    # --- Not outs (innings where the player was NOT dismissed) ---
    dismissed_innings = session.query(
        Delivery.match_id,
        Delivery.innings,
    ).filter(
        Delivery.player_dismissed == player_name,
        Delivery.wicket_kind != "retired hurt",
    ).distinct().all()

    dismissed_set = {(d.match_id, d.innings) for d in dismissed_innings}
    not_outs = sum(
        1 for row in innings_runs
        if (row.match_id, row.innings) not in dismissed_set
    )

    # --- Matches played (unique match IDs where they batted) ---
    matches_played = session.query(
        func.count(distinct(Delivery.match_id))
    ).filter(
        Delivery.batter == player_name,
    ).scalar() or 0

    # --- Computed stats ---
    dismissals = innings_count - not_outs
    average = round(total_runs / dismissals, 2) if dismissals > 0 else float(total_runs)
    strike_rate = round((total_runs / balls_faced) * 100, 2) if balls_faced > 0 else 0.0

    return {
        "name": player_name,
        "matches": matches_played,
        "innings": innings_count,
        "total_runs": total_runs,
        "balls_faced": balls_faced,
        "average": average,
        "strike_rate": strike_rate,
        "highest_score": highest_score,
        "fifties": fifties,
        "hundreds": hundreds,
        "fours": fours,
        "sixes": sixes,
        "not_outs": not_outs,
        "ducks": ducks,
    }


def get_player_bowling_stats(session: Session, player_name: str) -> dict:
    """
    Compute bowling statistics for a player.

    Returns:
        {
            "name": "JJ Bumrah",
            "matches": 120,
            "overs_bowled": 450.2,
            "runs_conceded": 3500,
            "wickets": 145,
            "economy": 7.77,
            "bowling_average": 24.14,
            "bowling_strike_rate": 18.62,
            "best_figures": "4/20",
        }
    """
    logger.info("Computing bowling stats for: %s", player_name)

    # Bowler-credited wickets in cricket exclude run outs, retired hurt, retired out, obstructing the field
    BOWLER_WICKETS = ["bowled", "caught", "caught and bowled", "hit wicket", "lbw", "stumped"]

    # --- Aggregate bowling data ---
    bowling_agg = session.query(
        func.sum(Delivery.runs_total).label("runs_conceded"),
        func.count(Delivery.id).label("balls_bowled"),
        func.sum(case(
            (Delivery.wicket_kind.in_(BOWLER_WICKETS), 1),
            else_=0,
        )).label("wickets"),
    ).filter(
        Delivery.bowler == player_name,
    ).first()

    runs_conceded = bowling_agg.runs_conceded or 0
    total_balls = bowling_agg.balls_bowled or 0
    wickets = bowling_agg.wickets or 0

    # Count legal deliveries (exclude wides and no-balls for over count)
    legal_balls = session.query(
        func.count(Delivery.id)
    ).filter(
        Delivery.bowler == player_name,
        Delivery.extra_type.is_(None) | ~Delivery.extra_type.in_(["wides", "noballs"]),
    ).scalar() or 0

    # Overs bowled (6 legal balls = 1 over)
    overs = legal_balls // 6
    remaining_balls = legal_balls % 6
    overs_bowled = float(f"{overs}.{remaining_balls}")

    # --- Match-level wickets (for best figures) ---
    match_wickets = session.query(
        Delivery.match_id,
        Delivery.innings,
        func.sum(case(
            (Delivery.wicket_kind.in_(BOWLER_WICKETS), 1),
            else_=0,
        )).label("wickets"),
        func.sum(Delivery.runs_total).label("runs"),
    ).filter(
        Delivery.bowler == player_name,
    ).group_by(
        Delivery.match_id, Delivery.innings,
    ).all()

    # Best figures
    best_wickets = 0
    best_runs = 0
    for mw in match_wickets:
        if mw.wickets > best_wickets or (mw.wickets == best_wickets and mw.runs < best_runs):
            best_wickets = mw.wickets
            best_runs = mw.runs

    best_figures = f"{best_wickets}/{best_runs}" if best_wickets > 0 else "0/0"

    # Matches bowled in
    matches_bowled = session.query(
        func.count(distinct(Delivery.match_id))
    ).filter(
        Delivery.bowler == player_name,
    ).scalar() or 0

    # Computed stats
    economy = round((runs_conceded * 6) / legal_balls, 2) if legal_balls > 0 else 0.0
    bowling_average = round(runs_conceded / wickets, 2) if wickets > 0 else 0.0
    bowling_sr = round(legal_balls / wickets, 2) if wickets > 0 else 0.0

    return {
        "name": player_name,
        "matches": matches_bowled,
        "overs_bowled": overs_bowled,
        "runs_conceded": runs_conceded,
        "wickets": wickets,
        "economy": economy,
        "bowling_average": bowling_average,
        "bowling_strike_rate": bowling_sr,
        "best_figures": best_figures,
    }


def get_player_season_runs(session: Session, player_name: str) -> list[dict]:
    """
    Get season-wise run totals for a player.

    Returns a list of {"season": 2023, "runs": 639, "matches": 14}
    Used for plotting season trends.
    """
    results = session.query(
        Match.season,
        func.sum(Delivery.runs_batter).label("runs"),
        func.count(distinct(Delivery.match_id)).label("matches"),
    ).join(
        Match, Delivery.match_id == Match.id,
    ).filter(
        Delivery.batter == player_name,
    ).group_by(
        Match.season,
    ).order_by(
        Match.season,
    ).all()

    return [
        {"season": r.season, "runs": r.runs, "matches": r.matches}
        for r in results
    ]


def search_players(session: Session, query: str) -> list[str]:
    """
    Search for players by partial name match.

    Case-insensitive LIKE search. Returns up to 20 matches.
    """
    from backend.app.models.player import Player

    results = session.query(Player.name).filter(
        Player.name.ilike(f"%{query}%")
    ).order_by(Player.name).limit(20).all()

    return [r[0] for r in results]


def get_player_teams(session: Session, player_name: str) -> list[str]:
    """
    Get all unique teams a player has played for in the IPL.
    """
    # Batting teams
    batting_teams = session.query(Team.name).join(
        Delivery, Delivery.batting_team_id == Team.id
    ).filter(
        Delivery.batter == player_name
    ).distinct()

    # Bowling teams
    bowling_teams = session.query(Team.name).join(
        Delivery, Delivery.bowling_team_id == Team.id
    ).filter(
        Delivery.bowler == player_name
    ).distinct()

    # Fielding teams
    fielding_teams = session.query(Team.name).join(
        Delivery, Delivery.bowling_team_id == Team.id
    ).filter(
        Delivery.fielder == player_name
    ).distinct()

    # Combine all query results using union and sort
    all_teams = batting_teams.union(bowling_teams).union(fielding_teams).all()
    return sorted([t[0] for t in all_teams])
