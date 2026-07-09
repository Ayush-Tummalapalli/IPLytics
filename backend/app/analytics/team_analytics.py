"""
IPLytics — Team Analytics Service

WHY THIS FILE EXISTS:
    This module contains analytics functions for IPL teams.
    It computes win/loss records, win percentages, head-to-head
    records, and season-wise performance.

HOW IT WORKS:
    Queries the matches table (joined with teams) to compute
    aggregated team statistics. Uses SQLAlchemy's query API
    for efficient SQL-level aggregation.

WHERE IT FITS:
    Called by API routes, AI assistant, and frontend components
    for team dashboards, comparisons, and visualizations.
"""

import logging

from sqlalchemy import func, case, or_, and_, distinct
from sqlalchemy.orm import Session

from backend.app.models.match import Match
from backend.app.models.team import Team

logger = logging.getLogger(__name__)


def get_all_teams(session: Session) -> list[dict]:
    """
    Get all teams with their names and short names.

    Returns: [{"id": 1, "name": "Mumbai Indians", "short_name": "MI"}, ...]
    """
    teams = session.query(Team).order_by(Team.name).all()
    return [
        {"id": t.id, "name": t.name, "short_name": t.short_name}
        for t in teams
    ]


def get_team_stats(session: Session, team_name: str) -> dict:
    """
    Compute comprehensive statistics for a team.

    Returns:
        {
            "name": "Mumbai Indians",
            "short_name": "MI",
            "total_matches": 237,
            "wins": 133,
            "losses": 104,
            "no_results": 0,
            "win_percentage": 56.12,
            "titles": 5,
            "toss_wins": 120,
            "bat_first_wins": 55,
            "field_first_wins": 78,
        }
    """
    logger.info("Computing team stats for: %s", team_name)

    # Get team record
    team = session.query(Team).filter(Team.name == team_name).first()
    if not team:
        logger.warning("Team not found: %s", team_name)
        return {}

    team_id = team.id

    # --- Total matches played ---
    total_matches = session.query(func.count(Match.id)).filter(
        or_(Match.team1_id == team_id, Match.team2_id == team_id)
    ).scalar() or 0

    # --- Wins ---
    wins = session.query(func.count(Match.id)).filter(
        Match.winner_id == team_id
    ).scalar() or 0

    # --- No results (winner_id is NULL) ---
    no_results = session.query(func.count(Match.id)).filter(
        or_(Match.team1_id == team_id, Match.team2_id == team_id),
        Match.winner_id.is_(None),
    ).scalar() or 0

    losses = total_matches - wins - no_results

    # --- Win percentage ---
    win_pct = round((wins / total_matches) * 100, 2) if total_matches > 0 else 0.0

    # --- Toss wins ---
    toss_wins = session.query(func.count(Match.id)).filter(
        Match.toss_winner_id == team_id,
    ).scalar() or 0

    # --- Bat first wins ---
    # A team bats first if:
    # 1. They won the toss and chose to bat
    # OR
    # 2. The other team won the toss and chose to field (forcing them to bat first)
    bat_first_wins = session.query(func.count(Match.id)).filter(
        Match.winner_id == team_id,
        or_(
            and_(Match.toss_winner_id == team_id, Match.toss_decision == "bat"),
            and_(Match.toss_winner_id != team_id, Match.toss_decision == "field")
        )
    ).scalar() or 0

    # --- Field first wins (Chase wins) ---
    field_first_wins = wins - bat_first_wins

    # --- Titles (finals won — approximate by checking last match of each season) ---
    # A simpler approach: count seasons where the team won the final
    # We approximate this by finding matches with result containing 'win'
    # and the team winning — this is a rough estimate

    return {
        "name": team_name,
        "short_name": team.short_name,
        "total_matches": total_matches,
        "wins": wins,
        "losses": losses,
        "no_results": no_results,
        "win_percentage": win_pct,
        "toss_wins": toss_wins,
        "bat_first_wins": bat_first_wins,
        "field_first_wins": field_first_wins,
    }


def get_team_season_performance(session: Session, team_name: str) -> list[dict]:
    """
    Get season-wise performance for a team.

    Returns:
        [
            {"season": 2023, "matches": 16, "wins": 11, "losses": 5,
             "win_percentage": 68.75},
            ...
        ]
    """
    team = session.query(Team).filter(Team.name == team_name).first()
    if not team:
        return []

    team_id = team.id

    # Get all seasons this team played in
    seasons = session.query(
        Match.season,
        func.count(Match.id).label("matches"),
        func.sum(case((Match.winner_id == team_id, 1), else_=0)).label("wins"),
        func.sum(case((Match.winner_id.is_(None), 1), else_=0)).label("no_results"),
    ).filter(
        or_(Match.team1_id == team_id, Match.team2_id == team_id)
    ).group_by(
        Match.season,
    ).order_by(
        Match.season,
    ).all()

    return [
        {
            "season": s.season,
            "matches": s.matches,
            "wins": s.wins,
            "losses": s.matches - s.wins - s.no_results,
            "no_results": s.no_results,
            "win_percentage": round((s.wins / s.matches) * 100, 2) if s.matches > 0 else 0.0,
        }
        for s in seasons
    ]


def get_head_to_head(session: Session, team1_name: str, team2_name: str) -> dict:
    """
    Get head-to-head record between two teams.

    Returns:
        {
            "team1": "Mumbai Indians",
            "team2": "Chennai Super Kings",
            "total_matches": 35,
            "team1_wins": 20,
            "team2_wins": 15,
            "no_results": 0,
        }
    """
    t1 = session.query(Team).filter(Team.name == team1_name).first()
    t2 = session.query(Team).filter(Team.name == team2_name).first()

    if not t1 or not t2:
        return {}

    # Matches where both teams played
    h2h_matches = session.query(Match).filter(
        or_(
            and_(Match.team1_id == t1.id, Match.team2_id == t2.id),
            and_(Match.team1_id == t2.id, Match.team2_id == t1.id),
        )
    ).all()

    total = len(h2h_matches)
    t1_wins = sum(1 for m in h2h_matches if m.winner_id == t1.id)
    t2_wins = sum(1 for m in h2h_matches if m.winner_id == t2.id)
    no_results = total - t1_wins - t2_wins

    return {
        "team1": team1_name,
        "team2": team2_name,
        "total_matches": total,
        "team1_wins": t1_wins,
        "team2_wins": t2_wins,
        "no_results": no_results,
    }


def search_teams(session: Session, query: str) -> list[dict]:
    """
    Search teams by partial name or short name match.
    """
    results = session.query(Team).filter(
        or_(
            Team.name.ilike(f"%{query}%"),
            Team.short_name.ilike(f"%{query}%"),
        )
    ).order_by(Team.name).all()

    return [
        {"id": t.id, "name": t.name, "short_name": t.short_name}
        for t in results
    ]


HOME_VENUES = {
    "Chennai Super Kings": ["MA Chidambaram Stadium", "MA Chidambaram Stadium, Chepauk", "MA Chidambaram Stadium, Chepauk, Chennai"],
    "Mumbai Indians": ["Wankhede Stadium", "Wankhede Stadium, Mumbai"],
    "Royal Challengers Bengaluru": ["M Chinnaswamy Stadium", "M.Chinnaswamy Stadium"],
    "Royal Challengers Bangalore": ["M Chinnaswamy Stadium", "M.Chinnaswamy Stadium"],
    "Kolkata Knight Riders": ["Eden Gardens", "Eden Gardens, Kolkata"],
    "Sunrisers Hyderabad": ["Rajiv Gandhi International Stadium", "Rajiv Gandhi International Stadium, Uppal"],
    "Delhi Capitals": ["Arun Jaitley Stadium", "Feroz Shah Kotla"],
    "Delhi Daredevils": ["Arun Jaitley Stadium", "Feroz Shah Kotla"],
    "Rajasthan Royals": ["Sawai Mansingh Stadium"],
    "Punjab Kings": ["Punjab Cricket Association IS Bindra Stadium, Mohali", "Punjab Cricket Association Stadium, Mohali"],
    "Kings XI Punjab": ["Punjab Cricket Association IS Bindra Stadium, Mohali", "Punjab Cricket Association Stadium, Mohali"],
    "Lucknow Super Giants": ["Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium", "Ekana Cricket Stadium"],
    "Gujarat Titans": ["Narendra Modi Stadium"]
}


def get_team_home_away_stats(session: Session, team_name: str, team_id: int) -> dict:
    """Compute win/loss metrics split by home venue vs away/neutral venues."""
    home_names = HOME_VENUES.get(team_name, [])
    if not home_names and "Royal Challengers" in team_name:
        home_names = HOME_VENUES.get("Royal Challengers Bengaluru", [])
    elif not home_names and "Delhi" in team_name:
        home_names = HOME_VENUES.get("Delhi Capitals", [])
    elif not home_names and "Punjab" in team_name:
        home_names = HOME_VENUES.get("Punjab Kings", [])

    if not home_names:
        return {}

    all_matches = session.query(Match).filter(
        or_(Match.team1_id == team_id, Match.team2_id == team_id)
    ).all()

    home_matches = []
    away_matches = []

    for m in all_matches:
        is_home = False
        for name in home_names:
            if name.lower() in (m.venue or "").lower():
                is_home = True
                break
        if is_home:
            home_matches.append(m)
        else:
            away_matches.append(m)

    def compute_split(matches):
        tot = len(matches)
        if tot == 0:
            return {"matches": 0, "wins": 0, "losses": 0, "win_pct": 0.0}
        wins = sum(1 for m in matches if m.winner_id == team_id)
        no_res = sum(1 for m in matches if m.winner_id is None)
        losses = tot - wins - no_res
        win_pct = round((wins / tot) * 100, 2)
        return {
            "matches": tot,
            "wins": wins,
            "losses": losses,
            "win_pct": win_pct
        }

    return {
        "home": compute_split(home_matches),
        "away": compute_split(away_matches)
    }


def get_team_opponents_stats(session: Session, team_id: int) -> list[dict]:
    """Compute win/loss ratios against every other opponent franchise dynamically."""
    matches = session.query(
        Match.id,
        Match.team1_id,
        Match.team2_id,
        Match.winner_id
    ).filter(
        or_(Match.team1_id == team_id, Match.team2_id == team_id)
    ).all()

    opponents = {}
    teams = session.query(Team.id, Team.name, Team.short_name).all()
    team_names = {t.id: (t.name, t.short_name) for t in teams}

    for m in matches:
        opp_id = m.team2_id if m.team1_id == team_id else m.team1_id
        if opp_id not in team_names:
            continue
        
        opp_name, opp_short = team_names[opp_id]
        if opp_short not in opponents:
            opponents[opp_short] = {
                "opponent": opp_name,
                "short_name": opp_short,
                "matches": 0,
                "wins": 0,
                "losses": 0,
                "no_results": 0
            }
            
        stats = opponents[opp_short]
        stats["matches"] += 1
        if m.winner_id == team_id:
            stats["wins"] += 1
        elif m.winner_id is None:
            stats["no_results"] += 1
        else:
            stats["losses"] += 1

    results = []
    for opp, stats in opponents.items():
        tot = stats["matches"]
        stats["win_pct"] = round((stats["wins"] / tot) * 100, 2) if tot > 0 else 0.0
        results.append(stats)

    results.sort(key=lambda x: x["matches"], reverse=True)
    return results
