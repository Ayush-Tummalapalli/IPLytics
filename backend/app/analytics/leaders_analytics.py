"""
IPLytics — Leaderboards & Stats Analytics Service

This module computes season-wise Cap winners and Top 10 leaderboards for batting
and bowling stats dynamically from the matches and deliveries tables.
"""

import logging
from sqlalchemy import func, case, and_, desc, asc, distinct
from sqlalchemy.orm import Session

from backend.app.models.delivery import Delivery
from backend.app.models.match import Match

logger = logging.getLogger(__name__)

def get_ipl_leaders(session: Session) -> dict:
    logger.info("Computing dynamically calculated IPL leaderboards...")

    # 1. Orange Cap Winners (Top run-scorer per season)
    season_runs = (
        session.query(
            Match.season.label("season"),
            Delivery.batter.label("batter"),
            func.sum(Delivery.runs_batter).label("runs")
        )
        .join(Delivery, Delivery.match_id == Match.id)
        .group_by(Match.season, Delivery.batter)
        .subquery()
    )
    all_season_runs = session.query(
        season_runs.c.season,
        season_runs.c.batter,
        season_runs.c.runs
    ).order_by(season_runs.c.season.desc(), season_runs.c.runs.desc()).all()

    orange_caps = []
    seen_seasons = set()
    for season, batter, runs in all_season_runs:
        if season not in seen_seasons:
            orange_caps.append({
                "season": int(season),
                "player": batter,
                "value": int(runs)
            })
            seen_seasons.add(season)

    # 2. Purple Cap Winners (Top wicket-taker per season, bowler-credited only)
    season_wkts = (
        session.query(
            Match.season.label("season"),
            Delivery.bowler.label("bowler"),
            func.count(Delivery.id).label("wickets")
        )
        .join(Delivery, Delivery.match_id == Match.id)
        .filter(
            Delivery.player_dismissed.isnot(None),
            Delivery.wicket_kind.in_(["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"])
        )
        .group_by(Match.season, Delivery.bowler)
        .subquery()
    )
    all_season_wkts = session.query(
        season_wkts.c.season,
        season_wkts.c.bowler,
        season_wkts.c.wickets
    ).order_by(season_wkts.c.season.desc(), season_wkts.c.wickets.desc()).all()

    purple_caps = []
    seen_seasons = set()
    for season, bowler, wickets in all_season_wkts:
        if season not in seen_seasons:
            purple_caps.append({
                "season": int(season),
                "player": bowler,
                "value": int(wickets)
            })
            seen_seasons.add(season)

    # 3. Top 10 Career Runs
    top_runs_agg = (
        session.query(Delivery.batter, func.sum(Delivery.runs_batter).label("runs"))
        .group_by(Delivery.batter)
        .order_by(desc("runs"))
        .limit(10)
        .all()
    )
    top_runs = [{"rank": i+1, "player": row[0], "value": int(row[1])} for i, row in enumerate(top_runs_agg)]

    # 4. Top 10 Career Wickets
    top_wkts_agg = (
        session.query(Delivery.bowler, func.count(Delivery.id).label("wickets"))
        .filter(
            Delivery.player_dismissed.isnot(None),
            Delivery.wicket_kind.in_(["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"])
        )
        .group_by(Delivery.bowler)
        .order_by(desc("wickets"))
        .limit(10)
        .all()
    )
    top_wickets = [{"rank": i+1, "player": row[0], "value": int(row[1])} for i, row in enumerate(top_wkts_agg)]

    # 5. Top 10 Sixes
    top_sixes_agg = (
        session.query(Delivery.batter, func.count(Delivery.id).label("sixes"))
        .filter(Delivery.runs_batter == 6)
        .group_by(Delivery.batter)
        .order_by(desc("sixes"))
        .limit(10)
        .all()
    )
    top_sixes = [{"rank": i+1, "player": row[0], "value": int(row[1])} for i, row in enumerate(top_sixes_agg)]

    # 6. Top 10 Batting Averages (min. 20 innings)
    runs_sub = (
        session.query(
            Delivery.batter,
            func.sum(Delivery.runs_batter).label("runs")
        )
        .group_by(Delivery.batter)
        .subquery()
    )
    dismissals_sub = (
        session.query(
            Delivery.player_dismissed.label("player"),
            func.count(Delivery.id).label("dismissals")
        )
        .filter(
            Delivery.wicket_kind.isnot(None),
            Delivery.wicket_kind != "retired hurt"
        )
        .group_by(Delivery.player_dismissed)
        .subquery()
    )
    innings_sub = (
        session.query(
            Delivery.batter,
            func.count(distinct(Delivery.match_id)).label("innings")
        )
        .group_by(Delivery.batter)
        .subquery()
    )
    top_avg_agg = (
        session.query(
            runs_sub.c.batter,
            runs_sub.c.runs,
            dismissals_sub.c.dismissals,
            (runs_sub.c.runs / case((dismissals_sub.c.dismissals == 0, 1), else_=dismissals_sub.c.dismissals)).label("average")
        )
        .join(dismissals_sub, runs_sub.c.batter == dismissals_sub.c.player)
        .join(innings_sub, runs_sub.c.batter == innings_sub.c.batter)
        .filter(innings_sub.c.innings >= 20)
        .order_by(desc("average"))
        .limit(10)
        .all()
    )
    top_batting_avg = [{
        "rank": i+1,
        "player": row[0],
        "runs": int(row[1]),
        "dismissals": int(row[2]),
        "value": float(round(row[3], 2))
    } for i, row in enumerate(top_avg_agg)]

    # 7. Top 10 Bowling Averages (min. 20 wickets)
    wkts_sub = (
        session.query(
            Delivery.bowler,
            func.count(Delivery.id).label("wickets")
        )
        .filter(
            Delivery.player_dismissed.isnot(None),
            Delivery.wicket_kind.in_(["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"])
        )
        .group_by(Delivery.bowler)
        .subquery()
    )
    runs_conceded_sub = (
        session.query(
            Delivery.bowler,
            func.sum(Delivery.runs_batter + case((Delivery.extra_type.in_(["wides", "noballs"]), Delivery.runs_extras), else_=0)).label("runs")
        )
        .group_by(Delivery.bowler)
        .subquery()
    )
    top_bowling_avg_agg = (
        session.query(
            wkts_sub.c.bowler,
            runs_conceded_sub.c.runs,
            wkts_sub.c.wickets,
            (runs_conceded_sub.c.runs / wkts_sub.c.wickets).label("average")
        )
        .join(runs_conceded_sub, wkts_sub.c.bowler == runs_conceded_sub.c.bowler)
        .filter(wkts_sub.c.wickets >= 20)
        .order_by(asc("average"))
        .limit(10)
        .all()
    )
    top_bowling_avg = [{
        "rank": i+1,
        "player": row[0],
        "runs_conceded": int(row[1]),
        "wickets": int(row[2]),
        "value": float(round(row[3], 2))
    } for i, row in enumerate(top_bowling_avg_agg)]

    return {
        "caps": {
            "orange": orange_caps,
            "purple": purple_caps
        },
        "leaderboards": {
            "runs": top_runs,
            "wickets": top_wickets,
            "sixes": top_sixes,
            "batting_average": top_batting_avg,
            "bowling_average": top_bowling_avg
        }
    }
