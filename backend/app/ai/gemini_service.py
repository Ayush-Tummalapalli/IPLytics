"""
IPLytics — AI Assistant Service (Google Gemini)

WHY THIS FILE EXISTS:
    This is the brain of the AI assistant. It takes a user's natural
    language question about IPL, fetches relevant data from our analytics
    engine, and sends it to Google Gemini with context so Gemini can
    generate an intelligent, data-backed answer.

HOW IT WORKS:
    1. User asks: "Who has the best batting average in IPL?"
    2. We detect what kind of question it is (player/team/venue/comparison)
    3. We fetch relevant data from our analytics functions
    4. We build a prompt with the data as context
    5. We send it to Gemini and return the response

    This is called "Retrieval-Augmented Generation" (RAG) — we don't
    rely on Gemini's training data alone, we GIVE it our actual data.

WHERE IT FITS:
    Called by the /ai/ask API endpoint (routes/ai.py) and displayed
    in the AI Assistant page (frontend/pages/5_🤖_AI_Assistant.py).
"""

import logging

import google.generativeai as genai
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.analytics.player_analytics import (
    get_player_batting_stats,
    get_player_bowling_stats,
    search_players,
)
from backend.app.analytics.team_analytics import (
    get_team_stats,
    get_head_to_head,
    get_all_teams,
    search_teams,
)
from backend.app.analytics.venue_analytics import (
    get_venue_stats,
    search_venues,
)

logger = logging.getLogger(__name__)

# --- Configure Gemini ---
genai.configure(api_key=settings.GEMINI_API_KEY)

# System prompt that tells Gemini who it is and how to behave
SYSTEM_PROMPT = """You are IPLytics AI — an expert IPL cricket analyst assistant.

IMPORTANT RULES:
1. You ONLY answer questions about IPL cricket. Politely decline unrelated questions.
2. When data is provided in the CONTEXT section, base your answer on that data.
3. Be specific — use actual numbers, stats, and seasons when available.
4. Keep answers concise but insightful (2-4 paragraphs max).
5. Use cricket terminology naturally (strike rate, economy, powerplay, etc.).
6. If the data seems incomplete, mention that but still give the best answer you can.
7. Format your response with markdown for readability.
8. Add brief analysis — don't just recite numbers, explain what they mean.
"""


def _extract_entities(question: str, db: Session) -> dict:
    """
    Extract player names, team names, and venue names from the question.

    This is a simple keyword-matching approach. We check if any known
    player/team/venue names appear in the question text.

    Returns: {"players": [...], "teams": [...], "venues": [...]}
    """
    question_lower = question.lower()
    entities: dict[str, list] = {"players": [], "teams": [], "venues": []}

    # --- Search for team names ---
    all_teams = get_all_teams(db)
    for team in all_teams:
        name_lower = team["name"].lower()
        short_lower = (team["short_name"] or "").lower()

        if name_lower in question_lower or (short_lower and short_lower in question_lower.split()):
            entities["teams"].append(team["name"])

    # --- Search for player names ---
    # Try to find player names by searching common patterns
    # We check for partial matches using our search function
    words = question.split()
    for i in range(len(words)):
        # Try 1-word, 2-word, and 3-word combinations
        for length in [1, 2, 3]:
            if i + length <= len(words):
                candidate = " ".join(words[i:i+length])
                # Clean up punctuation from candidate name
                candidate_clean = candidate.strip("?,.!-()\"'")
                if len(candidate_clean) > 3:  # Skip very short strings
                    matches = search_players(db, candidate_clean)
                    if matches and len(matches) <= 5:  # Only if reasonably specific
                        entities["players"].extend(matches[:2])

    # Deduplicate
    entities["players"] = list(set(entities["players"]))[:5]

    # --- Search for venue names ---
    venue_keywords = [w for w in words if len(w) > 4]
    for kw in venue_keywords:
        matches = search_venues(db, kw)
        if matches and len(matches) <= 3:
            entities["venues"].extend(matches[:1])

    entities["venues"] = list(set(entities["venues"]))[:3]

    logger.info("Extracted entities: %s", entities)
    return entities


def _get_seasons_summary(db: Session) -> str:
    """Get a summary of winners and runners-up for all seasons in the database."""
    from backend.app.models.match import Match
    try:
        # Get all unique seasons
        result = db.query(Match.season).distinct().order_by(Match.season).all()
        seasons = [r[0] for r in result]
        
        summary_lines = []
        for s in seasons:
            # Find the final match (last match of the season by date)
            final = db.query(Match).filter(Match.season == s).order_by(Match.date.desc()).first()
            if final and final.winner:
                winner = final.winner.name
                runner_up = final.team1.name if final.winner_id == final.team2_id else final.team2.name
                summary_lines.append(f"- **{s}**: Winner: {winner}, Runner-up: {runner_up}")
        return "\n".join(summary_lines)
    except Exception as e:
        logger.error("Error generating seasons summary: %s", e)
        return ""


# =================================================================
# COMPILING GENERAL DATABASE CONTEXT
# =================================================================

def _get_top_players_summary(db: Session) -> str:
    """Get all-time top batters and bowlers summary from the database."""
    from backend.app.models.delivery import Delivery
    from sqlalchemy import func, text
    try:
        # Top 5 run-scorers
        top_batters = db.query(
            Delivery.batter,
            func.sum(Delivery.runs_batter).label('runs')
        ).group_by(Delivery.batter).order_by(text('runs DESC')).limit(5).all()
        
        # Top 5 wicket-takers (bowler-credited wickets)
        wicket_kinds = ["bowled", "caught", "caught and bowled", "hit wicket", "lbw", "stumped"]
        top_bowlers = db.query(
            Delivery.bowler,
            func.count(Delivery.id).label('wickets')
        ).filter(
            Delivery.wicket_kind.in_(wicket_kinds)
        ).group_by(Delivery.bowler).order_by(text('wickets DESC')).limit(5).all()
        
        lines = ["**All-time Top 5 Batters (Most Runs in IPL history):**"]
        for idx, row in enumerate(top_batters, 1):
            lines.append(f"{idx}. {row.batter}: {row.runs:,} runs")
            
        lines.append("\n**All-time Top 5 Bowlers (Most Wickets in IPL history):**")
        for idx, row in enumerate(top_bowlers, 1):
            lines.append(f"{idx}. {row.bowler}: {row.wickets} wickets")
            
        return "\n".join(lines)
    except Exception as e:
        logger.error("Error generating top players summary: %s", e)
        return ""


def _get_venues_comparative_summary(db: Session) -> str:
    """Get all-time top venues by average first innings score and total matches."""
    from backend.app.models.match import Match
    from backend.app.models.delivery import Delivery
    from sqlalchemy import func, distinct, text
    try:
        # Top 5 by average 1st innings score (hosted >= 10 matches)
        query_score = db.query(
            Match.venue,
            func.count(distinct(Match.id)).label('matches'),
            (func.sum(Delivery.runs_total) / func.count(distinct(Match.id))).label('avg_first_innings')
        ).join(Delivery, Delivery.match_id == Match.id).filter(
            Delivery.innings == 1,
            Match.venue != "Unknown"
        ).group_by(Match.venue).having(
            func.count(distinct(Match.id)) >= 10
        ).order_by(text('avg_first_innings DESC')).limit(5)
        
        lines = ["**Top 5 Venues by Highest Average 1st Innings Score (min 10 matches hosted):**"]
        for idx, row in enumerate(query_score.all(), 1):
            avg_score = round(float(row.avg_first_innings), 1)
            lines.append(f"{idx}. {row.venue}: {avg_score} runs (across {row.matches} matches)")
            
        # Top 5 by total matches hosted
        query_count = db.query(
            Match.venue,
            func.count(Match.id).label('matches')
        ).filter(
            Match.venue != "Unknown"
        ).group_by(Match.venue).order_by(text('matches DESC')).limit(5)
        
        lines.append("\n**Top 5 Venues by Total Matches Hosted in IPL:**")
        for idx, row in enumerate(query_count.all(), 1):
            lines.append(f"{idx}. {row.venue}: {row.matches} matches")
            
        return "\n".join(lines)
    except Exception as e:
        logger.error("Error generating venue comparative summary: %s", e)
        return ""


def _build_context(question: str, entities: dict, db: Session) -> str:
    """
    Build a data context string by fetching relevant stats for
    the entities found in the question.

    This is the "Retrieval" part of RAG — we retrieve actual data
    from our database and include it in the prompt.
    """
    context_parts = []

    # --- Player Data ---
    for player_name in entities["players"]:
        batting = get_player_batting_stats(db, player_name)
        if batting["matches"] > 0:
            context_parts.append(f"""
### Player: {player_name}
**Batting:** {batting['matches']} matches, {batting['total_runs']} runs, 
Avg: {batting['average']}, SR: {batting['strike_rate']}, 
HS: {batting['highest_score']}, 50s: {batting['fifties']}, 100s: {batting['hundreds']},
4s: {batting['fours']}, 6s: {batting['sixes']}, Not Outs: {batting['not_outs']}""")

            bowling = get_player_bowling_stats(db, player_name)
            if bowling["wickets"] > 0:
                context_parts.append(f"""**Bowling:** {bowling['wickets']} wickets, 
Economy: {bowling['economy']}, Avg: {bowling['bowling_average']}, 
Best: {bowling['best_figures']}""")

    # --- Team Data ---
    for team_name in entities["teams"]:
        stats = get_team_stats(db, team_name)
        if stats:
            context_parts.append(f"""
### Team: {stats['name']} ({stats['short_name']})
Matches: {stats['total_matches']}, Wins: {stats['wins']}, 
Losses: {stats['losses']}, Win%: {stats['win_percentage']}%,
Toss Wins: {stats['toss_wins']}, Bat First Wins: {stats['bat_first_wins']}, 
Chase Wins: {stats['field_first_wins']}""")

    # --- Head-to-Head (if 2 teams mentioned) ---
    if len(entities["teams"]) == 2:
        h2h = get_head_to_head(db, entities["teams"][0], entities["teams"][1])
        if h2h:
            context_parts.append(f"""
### Head-to-Head: {h2h['team1']} vs {h2h['team2']}
Total: {h2h['total_matches']} matches, 
{h2h['team1']}: {h2h['team1_wins']} wins, 
{h2h['team2']}: {h2h['team2_wins']} wins""")

    # --- Venue Data ---
    for venue_name in entities["venues"]:
        stats = get_venue_stats(db, venue_name)
        if stats.get("total_matches", 0) > 0:
            context_parts.append(f"""
### Venue: {stats['venue']} ({stats['city']})
Matches: {stats['total_matches']}, Avg 1st Innings: {stats['avg_first_innings_score']},
Avg 2nd Innings: {stats['avg_second_innings_score']}, 
Highest: {stats['highest_total']}, Lowest: {stats['lowest_total']},
Chase Success: {stats['chase_success_rate']}%""")

    # --- Season/Year-specific Context ---
    import re
    # Target keywords specifically related to season outcomes/champions
    year_keywords = ["winner", "champion", "runners-up", "finalist", "finalists", "champions", "season winner", "season champions"]
    has_year_kw = any(kw in question.lower() for kw in year_keywords)
    has_year_number = any(2008 <= int(n) <= 2025 for n in re.findall(r'\b\d{4}\b', question))
    
    if has_year_kw or has_year_number:
        summary = _get_seasons_summary(db)
        if summary:
            context_parts.append(f"""
### Season Winners & Runners-up History (2008-2025):
{summary}""")

    # --- Fallback to General Comparative Aggregates when no specific context matches ---
    if not context_parts:
        logger.info("No specific entities matched. Loading general database aggregates for fallback.")
        players_sum = _get_top_players_summary(db)
        venues_sum = _get_venues_comparative_summary(db)
        seasons_sum = _get_seasons_summary(db)
        
        context_parts.append(f"""
### General IPL Database Aggregates & History (2008-2025)

{players_sum}

{venues_sum}

### Season Winners & Runners-up History (2008-2025):
{seasons_sum}""")

    return "## DATA FROM DATABASE\n" + "\n".join(context_parts)


def ask_question(question: str, db: Session) -> str:
    """
    Main entry point — takes a natural language question,
    fetches relevant data, and gets Gemini's analysis.

    Args:
        question: The user's question about IPL
        db: SQLAlchemy session for data retrieval

    Returns:
        Gemini's response as a markdown string
    """
    logger.info("AI question received: %s", question)

    # Step 1: Extract entities from the question
    entities = _extract_entities(question, db)

    # Step 2: Build data context
    context = _build_context(question, entities, db)

    # Step 3: Build the full prompt
    full_prompt = f"""{SYSTEM_PROMPT}

---

CONTEXT (Real IPL data from our database — 2008 to 2025):
{context}

---

USER QUESTION: {question}

Please provide a detailed, data-backed answer:"""

    # Step 4: Call Gemini
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(full_prompt)

        if response and response.text:
            logger.info("AI response generated (%d chars)", len(response.text))
            return response.text
        else:
            logger.warning("Empty response from Gemini")
            return "I couldn't generate a response. Please try rephrasing your question."

    except Exception as e:
        logger.error("Gemini API error: %s", e)

        if "API_KEY" in str(e).upper() or "INVALID" in str(e).upper():
            return (
                "⚠️ **Gemini API key is not configured.** "
                "Please set your `GEMINI_API_KEY` in the `.env` file.\n\n"
                "Get a free key at: https://aistudio.google.com/apikey"
            )

        return f"⚠️ AI service error: {e}"
