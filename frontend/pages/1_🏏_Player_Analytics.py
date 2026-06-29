"""
IPLytics Frontend — Player Analytics Page

WHY THIS PAGE EXISTS:
    This is the core player analysis view. Users select any IPL player
    and instantly see their career batting/bowling stats as metric cards,
    plus interactive charts for season-wise performance and boundary
    breakdown. It answers the question: "How good is this player, and
    how have they performed across seasons?"

HOW IT WORKS:
    1. On load, we fetch all player names from the backend and populate
       a selectbox.
    2. When a player is selected, we fetch their full stats (batting,
       bowling, season_runs) in a single cached API call.
    3. Stats are rendered as st.metric() cards in columns, and Plotly
       charts visualize trends and breakdowns.

WHERE IT FITS:
    frontend/pages/1_🏏_Player_Analytics.py
    Streamlit auto-discovers this as a sidebar page. The "1_" prefix
    controls sort order; the emoji makes the sidebar visually scannable.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from frontend.api_client import get_players, get_player_stats

# ── IPL-inspired color palette ──────────────────────────────────────
# Centralised here so every chart in this page is visually consistent.
COLOR_BATTING = "#e94560"   # IPL red — used for batting-related visuals
COLOR_BOWLING = "#0f3460"   # Deep blue — used for bowling visuals
COLOR_GOLD = "#f5a623"      # Gold accent — highlights & secondary bars
COLOR_BG_CARD = "#1a1a2e"   # Dark navy — card/page background tone


# ── Cached data loaders ────────────────────────────────────────────
# @st.cache_data keeps results in memory for `ttl` seconds, preventing
# redundant API calls on every Streamlit rerun (e.g. widget interaction).

@st.cache_data(ttl=300)
def load_players() -> list[str]:
    """Fetch the full player list once and cache for 5 minutes."""
    return get_players()


@st.cache_data(ttl=300)
def load_player_stats(name: str) -> dict | None:
    """Fetch a single player's stats and cache for 5 minutes."""
    return get_player_stats(name)


# ── Page configuration ──────────────────────────────────────────────
# Must be the FIRST Streamlit command; sets browser tab title + layout.
st.set_page_config(
    page_title="Player Analytics | IPLytics",
    page_icon="🏏",
    layout="wide",
)


def _safe(value, fallback="N/A"):
    """Return the value if it's not None, otherwise return the fallback.

    WHY: Backend may return None for stats that don't exist (e.g. a
    pure batsman with no bowling figures). We never want the UI to
    show 'None' — always a readable fallback.
    """
    return value if value is not None else fallback


def render_batting_metrics(batting: dict) -> None:
    """Display a row of key batting statistics as metric cards.

    WHY six metrics: These are the numbers any cricket fan checks first
    when evaluating a batsman — volume (matches, runs), quality
    (average, strike rate), and milestones (50s, 100s).
    """
    st.subheader("🏏 Batting Statistics")

    cols = st.columns(6)
    metrics = [
        ("Matches", _safe(batting.get("matches")), None),
        ("Runs", _safe(batting.get("total_runs")), None),
        ("Average", _safe(batting.get("average")), None),
        ("Strike Rate", _safe(batting.get("strike_rate")), None),
        ("50s", _safe(batting.get("fifties")), None),
        ("100s", _safe(batting.get("hundreds")), None),
    ]
    for col, (label, value, delta) in zip(cols, metrics):
        col.metric(label=label, value=value, delta=delta)


def render_bowling_metrics(bowling: dict) -> None:
    """Display a row of key bowling statistics as metric cards.

    WHY four metrics: Wickets measure impact, economy shows control,
    bowling average shows consistency, and best figures capture peak
    performance — the essential bowling quartet.
    """
    st.subheader("🎳 Bowling Statistics")

    cols = st.columns(4)
    metrics = [
        ("Wickets", _safe(bowling.get("wickets"))),
        ("Economy", _safe(bowling.get("economy"))),
        ("Bowling Avg", _safe(bowling.get("bowling_average"))),
        ("Best Figures", _safe(bowling.get("best_figures"))),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label=label, value=value)


def render_season_runs_chart(season_runs: list[dict], player_name: str) -> None:
    """Plot a bar chart of runs scored per IPL season.

    WHY a bar chart: Season-wise runs are discrete yearly totals — bars
    make it easy to compare magnitudes across years. We overlay a text
    label on each bar so exact values are readable without hovering.
    """
    if not season_runs:
        st.info("No season-wise run data available for this player.")
        return

    df = pd.DataFrame(season_runs)
    # Ensure 'season' is treated as a categorical axis, not continuous
    df["season"] = df["season"].astype(str)

    fig = px.bar(
        df,
        x="season",
        y="runs",
        text="runs",
        title=f"Season-wise Runs — {player_name}",
        labels={"season": "Season", "runs": "Runs Scored"},
        template="plotly_dark",
        color_discrete_sequence=[COLOR_BATTING],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="Season",
        yaxis_title="Runs",
        showlegend=False,
        # Extra top margin so text labels above bars aren't clipped
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_boundary_chart(batting: dict, player_name: str) -> None:
    """Plot a grouped bar chart comparing fours and sixes.

    WHY fours vs sixes: This reveals a batsman's scoring style —
    accumulator (more fours) vs power-hitter (more sixes). A single
    grouped bar makes the comparison immediately obvious.
    """
    fours = batting.get("fours")
    sixes = batting.get("sixes")

    if fours is None and sixes is None:
        st.info("No boundary data available for this player.")
        return

    fours = fours or 0
    sixes = sixes or 0

    fig = go.Figure(
        data=[
            go.Bar(
                name="Fours",
                x=["Boundaries"],
                y=[fours],
                marker_color=COLOR_BATTING,
                text=[fours],
                textposition="outside",
            ),
            go.Bar(
                name="Sixes",
                x=["Boundaries"],
                y=[sixes],
                marker_color=COLOR_GOLD,
                text=[sixes],
                textposition="outside",
            ),
        ]
    )
    fig.update_layout(
        title=f"Fours vs Sixes — {player_name}",
        barmode="group",
        template="plotly_dark",
        yaxis_title="Count",
        showlegend=True,
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Main page layout ───────────────────────────────────────────────

def main() -> None:
    """Orchestrate the entire Player Analytics page."""

    # ── Header ──
    st.title("🏏 Player Analytics")
    st.caption("Deep-dive into any IPL player's career stats and trends.")
    st.divider()

    # ── Load player list ──
    players = load_players()

    if not players:
        # Graceful degradation: if backend is down or DB is empty,
        # the user sees a clear message instead of a broken page.
        st.warning(
            "⚠️ No players found. Please make sure the backend server "
            "is running and the database is populated."
        )
        return

    # ── Player selector ──
    selected_player = st.selectbox(
        "Select a Player",
        options=players,
        index=0,
        help="Start typing to search for a player by name.",
    )

    if not selected_player:
        st.info("👆 Pick a player from the dropdown to get started.")
        return

    # ── Fetch stats ──
    with st.spinner(f"Loading stats for **{selected_player}**…"):
        stats = load_player_stats(selected_player)

    if not stats:
        st.error(
            f"Could not load stats for **{selected_player}**. "
            "The backend may be down or this player has no data."
        )
        return

    # ── Display Teams ──
    player_teams = stats.get("teams", [])
    if player_teams:
        st.markdown(f"**Teams:** " + " • ".join([f"`{t}`" for t in player_teams]))
        st.write("")

    batting: dict = stats.get("batting", {})
    bowling: dict = stats.get("bowling", {})
    season_runs: list[dict] = stats.get("season_runs", [])

    # ── Metric cards ──
    render_batting_metrics(batting)
    st.divider()
    render_bowling_metrics(bowling)
    st.divider()

    # ── Charts side-by-side ──
    # Two columns keep the page compact: season trend on the left,
    # boundary breakdown on the right.
    col_season, col_boundary = st.columns(2)

    with col_season:
        render_season_runs_chart(season_runs, selected_player)

    with col_boundary:
        render_boundary_chart(batting, selected_player)


main()
