"""
IPLytics — Data Ingestion Pipeline (ETL) for Consolidated Dataset

WHY THIS FILE EXISTS:
    This script loads the new consolidated Kaggle IPL dataset (IPL.csv) into PostgreSQL.
    It cleans up and maps team names to 15 canonical teams, extracts unique players,
    and ingests matches and deliveries up to the 2025 season.

HOW TO RUN:
    From the project root directory:
        python -m backend.app.database.ingest
"""

import logging
import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# --- File Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DOWNLOADS_CSV = Path("/Users/ayush._.27/Downloads/IPL.csv")
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
FALLBACK_CSV = RAW_DATA_DIR / "IPL.csv"

# Canonical list of teams
CANONICAL_TEAMS = [
    {"name": "Royal Challengers Bengaluru", "short_name": "RCB"},
    {"name": "Sunrisers Hyderabad", "short_name": "SRH"},
    {"name": "Mumbai Indians", "short_name": "MI"},
    {"name": "Rising Pune Supergiant", "short_name": "RPS"},
    {"name": "Gujarat Lions", "short_name": "GL"},
    {"name": "Kolkata Knight Riders", "short_name": "KKR"},
    {"name": "Chennai Super Kings", "short_name": "CSK"},
    {"name": "Rajasthan Royals", "short_name": "RR"},
    {"name": "Delhi Capitals", "short_name": "DC"},
    {"name": "Punjab Kings", "short_name": "PBKS"},
    {"name": "Lucknow Super Giants", "short_name": "LSG"},
    {"name": "Gujarat Titans", "short_name": "GT"},
    {"name": "Deccan Chargers", "short_name": "DCH"},
    {"name": "Kochi Tuskers Kerala", "short_name": "KTK"},
    {"name": "Pune Warriors", "short_name": "PW"},
]

# Map all 19 raw team name variations to the 15 canonical teams
TEAM_CANONICAL_MAP = {
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Royal Challengers Bengaluru": "Royal Challengers Bengaluru",
    "Sunrisers Hyderabad": "Sunrisers Hyderabad",
    "Mumbai Indians": "Mumbai Indians",
    "Rising Pune Supergiant": "Rising Pune Supergiant",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
    "Gujarat Lions": "Gujarat Lions",
    "Kolkata Knight Riders": "Kolkata Knight Riders",
    "Chennai Super Kings": "Chennai Super Kings",
    "Rajasthan Royals": "Rajasthan Royals",
    "Delhi Capitals": "Delhi Capitals",
    "Delhi Daredevils": "Delhi Capitals",
    "Punjab Kings": "Punjab Kings",
    "Kings XI Punjab": "Punjab Kings",
    "Lucknow Super Giants": "Lucknow Super Giants",
    "Gujarat Titans": "Gujarat Titans",
    "Deccan Chargers": "Deccan Chargers",
    "Kochi Tuskers Kerala": "Kochi Tuskers Kerala",
    "Pune Warriors": "Pune Warriors",
}


def parse_season(season_val) -> int:
    """Parse season string to calendar year integer."""
    s = str(season_val).strip()
    if s == "2007/08":
        return 2008
    if s == "2009/10":
        return 2010
    if "/" in s:
        return int(s.split("/")[0])
    return int(s)


def parse_win_outcome(outcome_val) -> tuple[int, int]:
    """Parse win outcome string to (win_by_runs, win_by_wickets)."""
    if pd.isna(outcome_val):
        return 0, 0
    s = str(outcome_val).strip().lower()
    if "run" in s:
        try:
            runs = int("".join(filter(str.isdigit, s)))
            return runs, 0
        except ValueError:
            return 0, 0
    elif "wicket" in s:
        try:
            wicks = int("".join(filter(str.isdigit, s)))
            return 0, wicks
        except ValueError:
            return 0, 0
    return 0, 0


# =================================================================
# STEP 1: LOAD TEAMS
# =================================================================

def load_teams(session: Session) -> dict[str, int]:
    """
    Populate standard canonical teams and build raw team name to DB ID lookup.
    """
    from backend.app.models.team import Team

    logger.info("📋 Loading canonical teams...")

    db_team_id_by_canonical_name: dict[str, int] = {}

    for t in CANONICAL_TEAMS:
        team = Team(name=t["name"], short_name=t["short_name"])
        session.add(team)
        session.flush()
        db_team_id_by_canonical_name[t["name"]] = team.id

    session.commit()

    # Map raw names (including historical names) to canonical team database ID
    team_id_map: dict[str, int] = {}
    for raw_name, canonical_name in TEAM_CANONICAL_MAP.items():
        team_id_map[raw_name] = db_team_id_by_canonical_name[canonical_name]

    logger.info("✅ Loaded %d canonical teams with aliases mapping", len(db_team_id_by_canonical_name))
    return team_id_map


# =================================================================
# STEP 2: LOAD PLAYERS
# =================================================================

def load_players(df: pd.DataFrame, session: Session) -> int:
    """
    Load unique players from the deliveries DataFrame.
    """
    from backend.app.models.player import Player

    logger.info("📋 Extracting unique players from delivery columns...")

    player_names: set[str] = set()
    for col in ["batter", "non_striker", "bowler", "player_out"]:
        for name in df[col].dropna().unique():
            clean = str(name).strip()
            if clean and clean != "nan" and clean.lower() != "unknown":
                player_names.add(clean)

    logger.info("  Found %d unique players", len(player_names))

    # Batch insert players
    BATCH_SIZE = 500
    sorted_names = sorted(player_names)
    for i in range(0, len(sorted_names), BATCH_SIZE):
        batch = sorted_names[i : i + BATCH_SIZE]
        session.bulk_save_objects([Player(name=n) for n in batch])
        session.flush()

    session.commit()
    logger.info("✅ Loaded %d players", len(sorted_names))
    return len(sorted_names)


# =================================================================
# STEP 3: LOAD MATCHES
# =================================================================

def load_matches(df: pd.DataFrame, team_id_map: dict[str, int], session: Session) -> int:
    """
    Load matches from the grouped deliveries DataFrame.
    """
    from backend.app.models.match import Match

    logger.info("📋 Processing matches from deliveries data...")

    # Drop duplicates by match_id to get match-level meta-data
    matches_df = df.drop_duplicates("match_id")
    logger.info("  Found %d matches to ingest", len(matches_df))

    valid_rows: list[dict] = []
    skipped = 0

    # For mapping team1 and team2, we construct unique teams per match_id
    logger.info("  Computing team1 and team2 for each match...")
    match_teams_lookup = {}
    for match_id, group in df.groupby("match_id"):
        teams_in_match = sorted(list(set(group["batting_team"].dropna()) | set(group["bowling_team"].dropna())))
        if len(teams_in_match) == 2:
            match_teams_lookup[match_id] = (teams_in_match[0], teams_in_match[1])
        elif len(teams_in_match) == 1:
            match_teams_lookup[match_id] = (teams_in_match[0], teams_in_match[0])
        else:
            match_teams_lookup[match_id] = ("Unknown", "Unknown")

    for _, row in matches_df.iterrows():
        try:
            match_id = int(row["match_id"])
            team1_name, team2_name = match_teams_lookup.get(match_id, ("Unknown", "Unknown"))
            
            team1_id = team_id_map.get(team1_name)
            team2_id = team_id_map.get(team2_name)
            
            toss_winner_name = str(row.get("toss_winner", "Unknown")).strip()
            toss_winner_id = team_id_map.get(toss_winner_name)

            if not team1_id or not team2_id or not toss_winner_id:
                logger.warning(
                    "  Skipping match %d: unmapped team (t1=%s, t2=%s, toss=%s)",
                    match_id, team1_name, team2_name, toss_winner_name
                )
                skipped += 1
                continue

            winner_id = None
            won_by_name = str(row.get("match_won_by")).strip()
            if pd.notna(row.get("match_won_by")) and won_by_name != "Unknown":
                winner_id = team_id_map.get(won_by_name)

            # Date
            match_date = pd.to_datetime(row["date"]).date()

            # Result type
            res_type = str(row.get("result_type")).strip().lower()
            if pd.isna(row.get("result_type")) or res_type == "nan" or res_type == "unknown":
                result = "win" if winner_id else "no result"
            else:
                result = res_type  # 'tie', 'no result', or 'win'

            # DL applied
            method_val = str(row.get("method", "")).strip().upper()
            dl_applied = "D/L" in method_val or "DLS" in method_val

            # Win margins
            win_by_runs, win_by_wickets = parse_win_outcome(row.get("win_outcome"))

            # Player of match
            pom = str(row.get("player_of_match")).strip()
            if pd.isna(row.get("player_of_match")) or pom == "nan" or pom == "Unknown":
                pom = "Unknown"

            # City & Venue
            city = str(row.get("city")).strip()
            if pd.isna(row.get("city")) or city == "nan":
                city = "Unknown"
            venue = str(row.get("venue")).strip()
            if pd.isna(row.get("venue")) or venue == "nan":
                venue = "Unknown"

            # Target runs
            target_runs = None
            if pd.notna(row.get("runs_target")):
                try:
                    target_runs = int(float(row["runs_target"]))
                except ValueError:
                    pass

            valid_rows.append({
                "id": match_id,
                "season": int(row["parsed_season"]),
                "date": match_date,
                "city": city,
                "venue": venue,
                "team1_id": team1_id,
                "team2_id": team2_id,
                "toss_winner_id": toss_winner_id,
                "toss_decision": str(row.get("toss_decision", "field")).lower().strip(),
                "winner_id": winner_id,
                "result": result,
                "win_by_runs": win_by_runs,
                "win_by_wickets": win_by_wickets,
                "player_of_match": pom,
                "dl_applied": dl_applied,
                "target_runs": target_runs,
                "target_overs": 20 if target_runs else None,
            })

        except Exception as e:
            logger.warning("  Skipping match %s during validation: %s", row.get("match_id", "?"), e)
            skipped += 1

    logger.info("  Validated %d matches (%d skipped)", len(valid_rows), skipped)

    # Bulk insert matches
    BATCH_SIZE = 200
    loaded = 0
    for i in range(0, len(valid_rows), BATCH_SIZE):
        batch = valid_rows[i : i + BATCH_SIZE]
        session.bulk_save_objects([Match(**r) for r in batch])
        session.commit()
        loaded += len(batch)

        if loaded % 400 == 0:
            logger.info("  Matches inserted: %d / %d", loaded, len(valid_rows))

    logger.info("✅ Loaded %d matches (%d skipped)", loaded, skipped)
    return loaded


# =================================================================
# STEP 4: LOAD DELIVERIES
# =================================================================

def load_deliveries(
    df: pd.DataFrame,
    team_id_map: dict[str, int],
    valid_match_ids: set[int],
    session: Session,
) -> int:
    """
    Load ball-by-ball deliveries using high-speed COPY expert streaming protocol.
    """
    import io
    logger.info("📋 Preparing deliveries for COPY expert streaming...")

    # 1. Filter match IDs
    df_filtered = df[df["match_id"].isin(valid_match_ids)].copy()

    # 2. Map team names to IDs
    df_filtered["batting_team_clean"] = df_filtered["batting_team"].astype(str).str.strip()
    df_filtered["bowling_team_clean"] = df_filtered["bowling_team"].astype(str).str.strip()

    df_filtered["batting_team_id"] = df_filtered["batting_team_clean"].map(team_id_map)
    df_filtered["bowling_team_id"] = df_filtered["bowling_team_clean"].map(team_id_map)

    # Drop rows where teams didn't map correctly
    df_filtered = df_filtered.dropna(subset=["batting_team_id", "bowling_team_id"])

    # 3. Clean columns (null-handling)
    def clean_col(series, max_len=None):
        cleaned = series.fillna("").astype(str).str.strip()
        mask = cleaned.isin(["nan", "None", ""])
        cleaned = cleaned.where(~mask, None)
        if max_len:
            cleaned = cleaned.str.slice(0, max_len)
        return cleaned

    df_filtered["wicket_kind"] = clean_col(df_filtered["wicket_kind"])
    df_filtered["player_dismissed"] = clean_col(df_filtered["player_out"])
    df_filtered["fielder"] = clean_col(df_filtered["fielders"], 100)
    df_filtered["extra_type"] = clean_col(df_filtered["extra_type"], 20)

    # 4. Filter columns and order them exactly for the COPY command
    cols_to_copy = [
        "match_id", "innings", "over", "ball", "batting_team_id", "bowling_team_id",
        "batter", "non_striker", "bowler", "runs_batter", "runs_extras", "runs_total",
        "extra_type", "wicket_kind", "player_dismissed", "fielder"
    ]
    df_copy = df_filtered[cols_to_copy].copy()

    # Force column data types to match DB schema
    int_cols = ["match_id", "innings", "over", "ball", "batting_team_id", "bowling_team_id", "runs_batter", "runs_extras", "runs_total"]
    for col in int_cols:
        df_copy[col] = df_copy[col].astype(int)

    str_cols = ["batter", "non_striker", "bowler"]
    for col in str_cols:
        df_copy[col] = df_copy[col].astype(str).str.strip()

    # Convert to in-memory tab-separated buffer
    logger.info("  Preparing streaming buffer for COPY protocol...")
    buf = io.StringIO()
    df_copy.to_csv(buf, header=False, index=False, sep='\t', na_rep='\\N')
    buf.seek(0)

    # 5. Execute copy_expert using raw psycopg2 connection
    logger.info("  Streaming %d deliveries into Neon using COPY expert...", len(df_copy))
    raw_conn = session.connection().connection
    cursor = raw_conn.cursor()
    cursor.copy_expert(
        "COPY deliveries (match_id, innings, \"over\", ball, batting_team_id, bowling_team_id, batter, non_striker, bowler, runs_batter, runs_extras, runs_total, extra_type, wicket_kind, player_dismissed, fielder) FROM STDIN WITH NULL AS '\\N'",
        buf
    )
    raw_conn.commit()
    logger.info("✅ Successfully loaded %d deliveries!", len(df_copy))
    return len(df_copy)


# =================================================================
# MAIN PIPELINE
# =================================================================

def clear_existing_data(session: Session) -> None:
    """Clear all existing data from tables (in correct FK order)."""
    logger.warning("🗑️  Clearing existing data...")
    session.execute(text("DELETE FROM deliveries"))
    session.execute(text("DELETE FROM matches"))
    session.execute(text("DELETE FROM players"))
    session.execute(text("DELETE FROM teams"))
    session.commit()
    logger.info("Existing data cleared.")


def run_pipeline() -> None:
    """Execute the full ETL pipeline."""
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("🏏 IPLytics Data Ingestion Pipeline (Consolidated)")
    logger.info("=" * 60)

    # --- Step 0: Find input dataset file ---
    csv_file = DOWNLOADS_CSV if DOWNLOADS_CSV.exists() else FALLBACK_CSV
    if not csv_file.exists():
        logger.error("❌ Required IPL.csv not found at %s or %s", DOWNLOADS_CSV, FALLBACK_CSV)
        sys.exit(1)
    
    logger.info("✅ Found dataset at: %s", csv_file)

    # --- Step 1: Read CSV ---
    logger.info("📖 Reading %s into memory...", csv_file.name)
    df = pd.read_csv(csv_file)
    logger.info("  Read %d rows from CSV", len(df))

    # --- Step 2: Parse Season and Filter <= 2025 ---
    logger.info("🧹 Parsing seasons and filtering data <= 2025 season...")
    df["parsed_season"] = df["season"].apply(parse_season)
    df = df[df["parsed_season"] <= 2025]
    logger.info("  Filtered to %d rows matching seasons up to 2025", len(df))

    # --- Connect to database ---
    from backend.app.database.connection import SessionLocal
    session = SessionLocal()

    try:
        # Clear existing data (makes script idempotent)
        clear_existing_data(session)

        # Step 3: Load teams
        team_id_map = load_teams(session)

        # Step 4: Load players
        player_count = load_players(df, session)

        # Step 5: Load matches
        match_count = load_matches(df, team_id_map, session)

        # Step 6: Get the set of match IDs actually in the DB
        result = session.execute(text("SELECT id FROM matches"))
        valid_match_ids = {row[0] for row in result}
        logger.info("📋 %d valid match IDs in database", len(valid_match_ids))

        # Step 7: Load deliveries (only for valid matches)
        delivery_count = load_deliveries(df, team_id_map, valid_match_ids, session)

        # --- Summary ---
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info("🏏 IPLytics Data Ingestion Complete!")
        logger.info("=" * 60)
        logger.info("  Teams:      %d", len(TEAM_CANONICAL_MAP))
        logger.info("  Players:    %d", player_count)
        logger.info("  Matches:    %d", match_count)
        logger.info("  Deliveries: %d", delivery_count)
        logger.info("  Time:       %.1f seconds", elapsed)
        logger.info("=" * 60)

    except Exception as e:
        session.rollback()
        logger.error("❌ Pipeline failed: %s", e, exc_info=True)
        sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    run_pipeline()
