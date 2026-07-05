"""
IPLytics — Trivia & Facts Analytics Service

This module computes interesting facts and trivia dynamically from the matches
and deliveries tables in the database.
"""

import logging
from sqlalchemy import func, case, and_, desc, asc, distinct
from sqlalchemy.orm import Session

from backend.app.models.delivery import Delivery
from backend.app.models.match import Match
from backend.app.models.team import Team

logger = logging.getLogger(__name__)

def get_ipl_facts(session: Session) -> dict:
    logger.info("Computing dynamically calculated IPL facts...")

    # Helper function to get team details by ID
    def get_team_info(team_id):
        if not team_id:
            return {"name": "Unknown", "short_name": "UNK"}
        t = session.query(Team).filter(Team.id == team_id).first()
        if t:
            return {"name": t.name, "short_name": t.short_name}
        return {"name": "Unknown", "short_name": "UNK"}

    # Helper function to get match details
    def get_match_info(match_id):
        m = session.query(Match).filter(Match.id == match_id).first()
        if m:
            t1 = get_team_info(m.team1_id)
            t2 = get_team_info(m.team2_id)
            return {
                "season": m.season,
                "venue": m.venue,
                "city": m.city,
                "team1": t1,
                "team2": t2,
                "date": str(m.date)
            }
        return {}

    # 1. Total Matches
    total_matches = session.query(func.count(Match.id)).scalar() or 0

    # 2. Total Deliveries
    total_deliveries = session.query(func.count(Delivery.id)).scalar() or 0

    # 3. Total Runs
    total_runs = session.query(func.sum(Delivery.runs_total)).scalar() or 0

    # 4. Total Fours
    total_fours = session.query(func.count(Delivery.id)).filter(Delivery.runs_batter == 4).scalar() or 0

    # 5. Total Sixes
    total_sixes = session.query(func.count(Delivery.id)).filter(Delivery.runs_batter == 6).scalar() or 0

    # 6. Total Wickets (all dismissals)
    total_wickets = session.query(func.count(Delivery.id)).filter(Delivery.player_dismissed.isnot(None)).scalar() or 0

    # 7. Most Career Runs
    most_runs_agg = (
        session.query(Delivery.batter, func.sum(Delivery.runs_batter).label("runs"))
        .group_by(Delivery.batter)
        .order_by(desc("runs"))
        .first()
    )
    most_runs = {
        "player": most_runs_agg[0] if most_runs_agg else "Unknown",
        "value": int(most_runs_agg[1]) if most_runs_agg else 0
    }

    # 8. Most Career Wickets (bowler-credited only)
    most_wkts_agg = (
        session.query(Delivery.bowler, func.count(Delivery.id).label("wickets"))
        .filter(
            Delivery.player_dismissed.isnot(None),
            Delivery.wicket_kind.in_(["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"])
        )
        .group_by(Delivery.bowler)
        .order_by(desc("wickets"))
        .first()
    )
    most_wickets = {
        "player": most_wkts_agg[0] if most_wkts_agg else "Unknown",
        "value": int(most_wkts_agg[1]) if most_wkts_agg else 0
    }

    # 9. Highest Individual Innings Score
    highest_score_agg = (
        session.query(
            Delivery.match_id,
            Delivery.batter,
            func.sum(Delivery.runs_batter).label("runs"),
            Delivery.bowling_team_id
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.batter, Delivery.bowling_team_id)
        .order_by(desc("runs"))
        .first()
    )
    highest_score = {}
    if highest_score_agg:
        opp = get_team_info(highest_score_agg[3])
        m_info = get_match_info(highest_score_agg[0])
        highest_score = {
            "player": highest_score_agg[1],
            "value": int(highest_score_agg[2]),
            "opponent": opp,
            "match": m_info
        }

    # 10. Best Bowling Figures
    wickets_sub = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.bowler,
            func.count(Delivery.id).label("wickets")
        )
        .filter(
            Delivery.player_dismissed.isnot(None),
            Delivery.wicket_kind.in_(["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"])
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.bowler)
        .subquery()
    )
    runs_sub = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.bowler,
            func.sum(Delivery.runs_batter + case((Delivery.extra_type.in_(["wides", "noballs"]), Delivery.runs_extras), else_=0)).label("runs_conceded")
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.bowler)
        .subquery()
    )
    best_bowling_agg = (
        session.query(
            wickets_sub.c.bowler,
            wickets_sub.c.wickets,
            runs_sub.c.runs_conceded,
            wickets_sub.c.match_id
        )
        .join(
            runs_sub,
            and_(
                wickets_sub.c.match_id == runs_sub.c.match_id,
                wickets_sub.c.innings == runs_sub.c.innings,
                wickets_sub.c.bowler == runs_sub.c.bowler
            )
        )
        .order_by(desc(wickets_sub.c.wickets), asc(runs_sub.c.runs_conceded))
        .first()
    )
    best_bowling = {}
    if best_bowling_agg:
        m_info = get_match_info(best_bowling_agg[3])
        best_bowling = {
            "player": best_bowling_agg[0],
            "wickets": int(best_bowling_agg[1]),
            "runs": int(best_bowling_agg[2]),
            "match": m_info
        }

    # 11. Most POTM Awards
    potm_agg = (
        session.query(Match.player_of_match, func.count(Match.id).label("awards"))
        .filter(Match.player_of_match.isnot(None))
        .group_by(Match.player_of_match)
        .order_by(desc("awards"))
        .first()
    )
    most_potm = {
        "player": potm_agg[0] if potm_agg else "Unknown",
        "value": int(potm_agg[1]) if potm_agg else 0
    }

    # 12. Highest Team Total
    highest_team_agg = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.batting_team_id,
            func.sum(Delivery.runs_total).label("total_runs")
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.batting_team_id)
        .order_by(desc("total_runs"))
        .first()
    )
    highest_team = {}
    if highest_team_agg:
        team = get_team_info(highest_team_agg[2])
        m_info = get_match_info(highest_team_agg[0])
        # Find wickets fallen in that innings
        wkts = session.query(func.count(Delivery.id)).filter(
            Delivery.match_id == highest_team_agg[0],
            Delivery.innings == highest_team_agg[1],
            Delivery.player_dismissed.isnot(None)
        ).scalar() or 0
        highest_team = {
            "team": team,
            "runs": int(highest_team_agg[3]),
            "wickets": wkts,
            "match": m_info
        }

    # 13. Lowest Team Total (in completed innings of >= 10 overs, dl_applied = False)
    lowest_team_agg = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.batting_team_id,
            func.sum(Delivery.runs_total).label("total_runs")
        )
        .join(Match, Match.id == Delivery.match_id)
        .filter(Match.dl_applied == False)
        .group_by(Delivery.match_id, Delivery.innings, Delivery.batting_team_id)
        .having(func.count(Delivery.id) >= 60)
        .order_by(asc("total_runs"))
        .first()
    )
    lowest_team = {}
    if lowest_team_agg:
        team = get_team_info(lowest_team_agg[2])
        m_info = get_match_info(lowest_team_agg[0])
        wkts = session.query(func.count(Delivery.id)).filter(
            Delivery.match_id == lowest_team_agg[0],
            Delivery.innings == lowest_team_agg[1],
            Delivery.player_dismissed.isnot(None)
        ).scalar() or 0
        lowest_team = {
            "team": team,
            "runs": int(lowest_team_agg[3]),
            "wickets": wkts,
            "match": m_info
        }

    # 14. Most 5-Wicket Hauls
    fifer_sub = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.bowler,
            func.count(Delivery.id).label("wickets")
        )
        .filter(
            Delivery.player_dismissed.isnot(None),
            Delivery.wicket_kind.in_(["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"])
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.bowler)
        .having(func.count(Delivery.id) >= 5)
        .subquery()
    )
    fifers_agg = (
        session.query(fifer_sub.c.bowler, func.count(fifer_sub.c.match_id).label("cnt"))
        .group_by(fifer_sub.c.bowler)
        .order_by(desc("cnt"))
        .first()
    )
    most_fifers = {
        "player": fifers_agg[0] if fifers_agg else "Unknown",
        "value": int(fifers_agg[1]) if fifers_agg else 0
    }

    # 15. Most Duck Outs (0 runs and dismissed)
    duck_sub = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.batter,
            func.sum(Delivery.runs_batter).label("runs"),
            func.sum(case((Delivery.player_dismissed == Delivery.batter, 1), else_=0)).label("was_dismissed")
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.batter)
        .having(and_(func.sum(Delivery.runs_batter) == 0, func.sum(case((Delivery.player_dismissed == Delivery.batter, 1), else_=0)) > 0))
        .subquery()
    )
    ducks_agg = (
        session.query(duck_sub.c.batter, func.count(duck_sub.c.match_id).label("cnt"))
        .group_by(duck_sub.c.batter)
        .order_by(desc("cnt"))
        .first()
    )
    most_ducks = {
        "player": ducks_agg[0] if ducks_agg else "Unknown",
        "value": int(ducks_agg[1]) if ducks_agg else 0
    }

    # 16. Most Expensive Spell
    expensive_spell_agg = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.bowler,
            func.sum(Delivery.runs_batter + case((Delivery.extra_type.in_(["wides", "noballs"]), Delivery.runs_extras), else_=0)).label("runs_conceded")
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.bowler)
        .order_by(desc("runs_conceded"))
        .first()
    )
    expensive_spell = {}
    if expensive_spell_agg:
        m_info = get_match_info(expensive_spell_agg[0])
        # Count overs bowled in that spell
        balls = session.query(func.count(Delivery.id)).filter(
            Delivery.match_id == expensive_spell_agg[0],
            Delivery.innings == expensive_spell_agg[1],
            Delivery.bowler == expensive_spell_agg[2],
            Delivery.extra_type.is_(None) | (Delivery.extra_type != "wides")
        ).scalar() or 0
        overs = f"{balls // 6}.{balls % 6}"
        expensive_spell = {
            "player": expensive_spell_agg[2],
            "runs": int(expensive_spell_agg[3]),
            "overs": overs,
            "match": m_info
        }

    # 17. Largest Win Margin (Runs)
    large_win_agg = (
        session.query(Match.id, Match.winner_id, Match.win_by_runs)
        .order_by(desc(Match.win_by_runs))
        .first()
    )
    large_win_runs = {}
    if large_win_agg:
        team = get_team_info(large_win_agg[1])
        m_info = get_match_info(large_win_agg[0])
        large_win_runs = {
            "team": team,
            "value": int(large_win_agg[2]),
            "match": m_info
        }

    # 18. Highest Run Venue (Average score per match, min 10 matches)
    venue_runs_sub = (
        session.query(
            Match.venue,
            func.count(distinct(Match.id)).label("match_count"),
            func.sum(Delivery.runs_total).label("total_runs")
        )
        .join(Delivery, Delivery.match_id == Match.id)
        .group_by(Match.venue)
        .having(func.count(distinct(Match.id)) >= 10)
        .subquery()
    )
    venue_highest_agg = (
        session.query(
            venue_runs_sub.c.venue,
            (venue_runs_sub.c.total_runs / venue_runs_sub.c.match_count).label("avg_runs"),
            venue_runs_sub.c.match_count
        )
        .order_by(desc("avg_runs"))
        .first()
    )
    venue_highest = {
        "venue": venue_highest_agg[0] if venue_highest_agg else "Unknown",
        "value": float(round(venue_highest_agg[1], 2)) if venue_highest_agg else 0.0,
        "matches": int(venue_highest_agg[2]) if venue_highest_agg else 0
    }

    # 19. Most Toss Wins
    most_tosses_agg = (
        session.query(Match.toss_winner_id, func.count(Match.id).label("cnt"))
        .group_by(Match.toss_winner_id)
        .order_by(desc("cnt"))
        .first()
    )
    most_toss_wins = {}
    if most_tosses_agg:
        team = get_team_info(most_tosses_agg[0])
        most_toss_wins = {
            "team": team,
            "value": int(most_tosses_agg[1])
        }

    # 20. Best Chasing Venue (Percentage, min 10 matches)
    chase_cond = case(
        (and_(Match.toss_decision == 'field', Match.toss_winner_id == Match.winner_id), 1),
        (and_(Match.toss_decision == 'bat', Match.toss_winner_id != Match.winner_id, Match.winner_id.isnot(None)), 1),
        else_=0
    )
    venue_chase_agg = (
        session.query(
            Match.venue,
            func.count(Match.id).label("matches"),
            func.sum(chase_cond).label("chase_wins")
        )
        .filter(Match.result == 'win')
        .group_by(Match.venue)
        .having(func.count(Match.id) >= 10)
        .all()
    )
    best_chase_venue = {"venue": "Unknown", "value": 0.0, "matches": 0, "chase_wins": 0}
    if venue_chase_agg:
        sorted_chase = sorted(venue_chase_agg, key=lambda x: (x.chase_wins / x.matches), reverse=True)
        top = sorted_chase[0]
        best_chase_venue = {
            "venue": top.venue,
            "value": float(round((top.chase_wins / top.matches) * 100, 2)),
            "matches": int(top.matches),
            "chase_wins": int(top.chase_wins)
        }

    # 21. Most Match Wins
    most_wins_agg = (
        session.query(Match.winner_id, func.count(Match.id).label("cnt"))
        .filter(Match.winner_id.isnot(None))
        .group_by(Match.winner_id)
        .order_by(desc("cnt"))
        .first()
    )
    most_match_wins = {}
    if most_wins_agg:
        team = get_team_info(most_wins_agg[0])
        most_match_wins = {
            "team": team,
            "value": int(most_wins_agg[1])
        }

    # 22. Total Tie Matches (Super Overs)
    total_ties = session.query(func.count(Match.id)).filter(Match.result == 'tie').scalar() or 0

    # 23. Bat First vs Chase Ratio
    total_result_wins = session.query(func.count(Match.id)).filter(Match.result == 'win').scalar() or 1
    overall_chase_wins = session.query(func.sum(chase_cond)).filter(Match.result == 'win').scalar() or 0
    overall_bat_first_wins = total_result_wins - overall_chase_wins
    chase_ratio = float(round((overall_chase_wins / total_result_wins) * 100, 2))
    bat_first_ratio = float(round((overall_bat_first_wins / total_result_wins) * 100, 2))

    # 24. Most Centuries Scored
    century_sub = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.batter,
            func.sum(Delivery.runs_batter).label("runs")
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.batter)
        .having(func.sum(Delivery.runs_batter) >= 100)
        .subquery()
    )
    most_centuries_agg = (
        session.query(century_sub.c.batter, func.count(century_sub.c.match_id).label("cnt"))
        .group_by(century_sub.c.batter)
        .order_by(desc("cnt"))
        .first()
    )
    most_centuries = {
        "player": most_centuries_agg[0] if most_centuries_agg else "Unknown",
        "value": int(most_centuries_agg[1]) if most_centuries_agg else 0
    }

    # 25. Most Expensive Over
    expensive_over_agg = (
        session.query(
            Delivery.match_id,
            Delivery.innings,
            Delivery.over,
            Delivery.bowler,
            func.sum(Delivery.runs_total).label("runs")
        )
        .group_by(Delivery.match_id, Delivery.innings, Delivery.over, Delivery.bowler)
        .order_by(desc("runs"))
        .first()
    )
    expensive_over = {}
    if expensive_over_agg:
        m_info = get_match_info(expensive_over_agg[0])
        expensive_over = {
            "player": expensive_over_agg[3],
            "runs": int(expensive_over_agg[4]),
            "over": int(expensive_over_agg[2]) + 1,  # Convert 0-indexed over to 1-indexed
            "match": m_info
        }

    return {
        "totals": {
            "matches": total_matches,
            "deliveries": total_deliveries,
            "runs": total_runs,
            "fours": total_fours,
            "sixes": total_sixes,
            "wickets": total_wickets,
            "ties": total_ties
        },
        "records": {
            "most_runs": most_runs,
            "most_wickets": most_wickets,
            "highest_score": highest_score,
            "best_bowling": best_bowling,
            "most_potm": most_potm,
            "highest_team": highest_team,
            "lowest_team": lowest_team,
            "most_fifers": most_fifers,
            "most_ducks": most_ducks,
            "expensive_spell": expensive_spell,
            "large_win_runs": large_win_runs,
            "venue_highest": venue_highest,
            "most_toss_wins": most_toss_wins,
            "best_chase_venue": best_chase_venue,
            "most_match_wins": most_match_wins,
            "chase_ratio": chase_ratio,
            "bat_first_ratio": bat_first_ratio,
            "most_centuries": most_centuries,
            "expensive_over": expensive_over
        }
    }
