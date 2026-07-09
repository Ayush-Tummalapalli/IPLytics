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

from frontend.api_client import get_players, get_player_stats, get_ipl_leaders

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


@st.cache_data(ttl=600)
def load_ipl_leaders() -> dict | None:
    """Fetch the IPL Orange & Purple cap winners."""
    return get_ipl_leaders()


# ── Page configuration ──────────────────────────────────────────────
# Must be the FIRST Streamlit command; sets browser tab title + layout.
st.set_page_config(
    page_title="Player Analytics | IPLytics",
    page_icon="🏏",
    layout="wide",
)

# Custom CSS for premium styling (glassmorphic metric cards)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp, * {
        font-family: 'Outfit', sans-serif !important;
    }
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #e9456030;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.1);
        transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease, border-color 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #e9456080;
        box-shadow: 0 12px 30px rgba(233, 69, 96, 0.25);
    }
    div[data-testid="stMetric"] label {
        color: #8892b0 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e94560 !important;
        font-weight: 700;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23, #1a1a2e);
    }
    [data-testid="stSidebarNavItems"] {
        max-height: none !important;
    }
</style>
""", unsafe_allow_html=True)


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


def render_season_runs_chart(season_runs: list[dict], player_name: str, has_batted: bool) -> None:
    """Plot a premium area line chart of runs scored per IPL season."""
    if not has_batted:
        st.info("This player hasn't batted in his whole career")
        return
    if not season_runs:
        st.info("No season-wise run data available for this player.")
        return

    df = pd.DataFrame(season_runs)
    df["season"] = df["season"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["season"],
        y=df["runs"],
        mode="lines+markers",
        line=dict(shape="spline", smoothing=1.3, color="#e94560", width=4),
        marker=dict(size=8, color="#f5a623", symbol="circle", line=dict(color="#1a1a2e", width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(233, 69, 96, 0.15)",
        name="Runs Scored",
        text=df["runs"],
        hovertemplate="<b>Season %{x}</b><br>Runs: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title=f"📈 Season-wise Runs — {player_name}",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="#8892b0"),
            linecolor="rgba(255,255,255,0.1)"
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            gridwidth=1,
            zeroline=False,
            tickfont=dict(color="#8892b0")
        ),
        margin=dict(t=60, b=40, l=40, r=20),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_season_wickets_chart(season_wickets: list[dict], player_name: str, has_bowled: bool) -> None:
    """Plot a premium area line chart of wickets taken per IPL season."""
    if not has_bowled:
        st.info("This player hasn't bowled in his career")
        return
    if not season_wickets or sum(w.get("wickets", 0) for w in season_wickets) == 0:
        st.info("No season-wise wicket data available for this player.")
        return

    df = pd.DataFrame(season_wickets)
    df["season"] = df["season"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["season"],
        y=df["wickets"],
        mode="lines+markers",
        line=dict(shape="spline", smoothing=1.3, color="#b085f5", width=4),
        marker=dict(size=8, color="#00bcd4", symbol="circle", line=dict(color="#1a1a2e", width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(176, 133, 245, 0.15)",
        name="Wickets Taken",
        text=df["wickets"],
        hovertemplate="<b>Season %{x}</b><br>Wickets: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title=f"🎯 Season-wise Wickets — {player_name}",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="#8892b0"),
            linecolor="rgba(255,255,255,0.1)"
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            gridwidth=1,
            zeroline=False,
            tickfont=dict(color="#8892b0")
        ),
        margin=dict(t=60, b=40, l=40, r=20),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_consistency_charts(batting: dict, bowling: dict, player_name: str) -> None:
    """Render the batsman score distribution and bowler wickets distribution side-by-side."""
    st.markdown("### 🎯 Performance Consistency & Distribution")
    st.caption("Detailed breakdown of scores and wickets per match to analyze player consistency.")
    
    col_bat, col_bowl = st.columns(2)
    
    # ── Batting consistency ──
    with col_bat:
        runs_list = batting.get("runs_list", [])
        if runs_list:
            brackets = {
                "0-10 Runs": 0,
                "11-30 Runs": 0,
                "31-50 Runs": 0,
                "51-99 Runs": 0,
                "100+ Runs": 0
            }
            for runs in runs_list:
                if runs <= 10:
                    brackets["0-10 Runs"] += 1
                elif runs <= 30:
                    brackets["11-30 Runs"] += 1
                elif runs <= 50:
                    brackets["31-50 Runs"] += 1
                elif runs < 100:
                    brackets["51-99 Runs"] += 1
                else:
                    brackets["100+ Runs"] += 1
                    
            labels = list(brackets.keys())
            values = list(brackets.values())
            
            non_zero = [(l, v) for l, v in zip(labels, values) if v > 0]
            if non_zero:
                labels, values = zip(*non_zero)
                
            fig_bat = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker_colors=["#e94560", "#ff6b6b", "#f5a623", "#4ecdc4", "#10ac84"],
                textfont=dict(color="#ccd6f6", size=12),
                textinfo="percent",
            )])
            fig_bat.update_traces(textposition="inside")
            fig_bat.update_layout(
                title=f"🏏 Batting Score Split — {player_name}",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=50, b=20, l=20, r=20),
                height=350,
                legend=dict(font=dict(color="#ccd6f6"))
            )
            st.plotly_chart(fig_bat, use_container_width=True)
        else:
            st.info("No batting innings data available to analyze consistency.")
            
    # ── Bowling consistency ──
    with col_bowl:
        wickets_list = bowling.get("wickets_list", [])
        if wickets_list and bowling.get("matches", 0) > 0:
            brackets = {
                "0 Wickets": 0,
                "1-2 Wickets": 0,
                "3-4 Wickets": 0,
                "5+ Wickets": 0
            }
            for wkts in wickets_list:
                if wkts == 0:
                    brackets["0 Wickets"] += 1
                elif wkts <= 2:
                    brackets["1-2 Wickets"] += 1
                elif wkts <= 4:
                    brackets["3-4 Wickets"] += 1
                else:
                    brackets["5+ Wickets"] += 1
                    
            labels = list(brackets.keys())
            values = list(brackets.values())
            
            non_zero = [(l, v) for l, v in zip(labels, values) if v > 0]
            if non_zero:
                labels, values = zip(*non_zero)
                
            fig_bowl = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker_colors=["#48dbfb", "#b085f5", "#5f27cd", "#ff9ff3"],
                textfont=dict(color="#ccd6f6", size=12),
                textinfo="percent",
            )])
            fig_bowl.update_traces(textposition="inside")
            fig_bowl.update_layout(
                title=f"🎳 Bowling Wicket Split — {player_name}",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=50, b=20, l=20, r=20),
                height=350,
                legend=dict(font=dict(color="#ccd6f6"))
            )
            st.plotly_chart(fig_bowl, use_container_width=True)
        else:
            st.info("No bowling innings data available to analyze consistency.")


def generate_trophy_cabinet_html(batting: dict, bowling: dict, orange_seasons: list[str], purple_seasons: list[str]) -> str:
    """Generate HTML for visual trophy cabinet achievements."""
    runs = batting.get("total_runs", 0) or 0
    wkts = bowling.get("wickets", 0) or 0
    sixes = batting.get("sixes", 0) or 0
    hundreds = batting.get("hundreds", 0) or 0
    highest = batting.get("highest_score", 0) or 0
    
    # Calculate 5-wicket hauls from bowling wickets_list
    wkts_list = bowling.get("wickets_list", [])
    five_wkt_hauls = sum(1 for w in wkts_list if w >= 5) if wkts_list else 0

    badges = []
    
    # Orange Cap
    if orange_seasons:
        badges.append({
            "label": f"Orange Cap ({', '.join(orange_seasons)})",
            "emoji": "👑",
            "unlocked": True,
            "color": "linear-gradient(135deg, #f5a623 0%, #d4af37 100%)",
            "border": "#f5a623"
        })
    else:
        badges.append({
            "label": "Orange Cap Winner",
            "emoji": "👑",
            "unlocked": False,
            "color": "rgba(255,255,255,0.02)",
            "border": "rgba(255,255,255,0.05)"
        })
        
    # Purple Cap
    if purple_seasons:
        badges.append({
            "label": f"Purple Cap ({', '.join(purple_seasons)})",
            "emoji": "👑",
            "unlocked": True,
            "color": "linear-gradient(135deg, #b085f5 0%, #8e2de2 100%)",
            "border": "#b085f5"
        })
    else:
        badges.append({
            "label": "Purple Cap Winner",
            "emoji": "👑",
            "unlocked": False,
            "color": "rgba(255,255,255,0.02)",
            "border": "rgba(255,255,255,0.05)"
        })

    # 5000+ Runs Club
    if runs >= 5000:
        badges.append({
            "label": f"5000+ Runs Club ({runs:,} runs)",
            "emoji": "🏏",
            "unlocked": True,
            "color": "linear-gradient(135deg, #e94560 0%, #ff6b6b 100%)",
            "border": "#e94560"
        })
    else:
        badges.append({
            "label": "5000+ Runs Club",
            "emoji": "🏏",
            "unlocked": False,
            "color": "rgba(255,255,255,0.02)",
            "border": "rgba(255,255,255,0.05)"
        })

    # 200+ Sixes Club
    if sixes >= 200:
        badges.append({
            "label": f"200+ Sixes Club ({sixes} sixes)",
            "emoji": "💥",
            "unlocked": True,
            "color": "linear-gradient(135deg, #ff9f43 0%, #ff9f43bb 100%)",
            "border": "#ff9f43"
        })
    else:
        badges.append({
            "label": "200+ Sixes Club",
            "emoji": "💥",
            "unlocked": False,
            "color": "rgba(255,255,255,0.02)",
            "border": "rgba(255,255,255,0.05)"
        })

    # 150+ Wickets Club
    if wkts >= 150:
        badges.append({
            "label": f"150+ Wkts Club ({wkts} wickets)",
            "emoji": "🎳",
            "unlocked": True,
            "color": "linear-gradient(135deg, #00d2d3 0%, #01a3a4 100%)",
            "border": "#00d2d3"
        })
    else:
        badges.append({
            "label": "150+ Wickets Club",
            "emoji": "🎳",
            "unlocked": False,
            "color": "rgba(255,255,255,0.02)",
            "border": "rgba(255,255,255,0.05)"
        })

    # Centurion
    if hundreds >= 1 or highest >= 100:
        badges.append({
            "label": f"Centurion ({max(hundreds, 1)} x 100s)",
            "emoji": "💯",
            "unlocked": True,
            "color": "linear-gradient(135deg, #ee5253 0%, #ff6b6b 100%)",
            "border": "#ee5253"
        })
    else:
        badges.append({
            "label": "Centurion Club",
            "emoji": "💯",
            "unlocked": False,
            "color": "rgba(255,255,255,0.02)",
            "border": "rgba(255,255,255,0.05)"
        })

    # 5-Wicket Haul
    if five_wkt_hauls >= 1:
        badges.append({
            "label": f"5-Wkt Haul ({five_wkt_hauls} x 5-fers)",
            "emoji": "🖐️",
            "unlocked": True,
            "color": "linear-gradient(135deg, #10ac84 0%, #1dd1a1 100%)",
            "border": "#10ac84"
        })
    else:
        badges.append({
            "label": "5-Wicket Haul Club",
            "emoji": "🖐️",
            "unlocked": False,
            "color": "rgba(255,255,255,0.02)",
            "border": "rgba(255,255,255,0.05)"
        })

        # Generate custom cleaned HTML
    html_lines = [
        '<div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(245, 166, 35, 0.15); border-radius: 12px; padding: 1.25rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-top: 1.5rem; width: 100%;">',
        '<h5 style="margin: 0 0 1rem 0; color: #f5a623; font-size: 1.15rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; justify-content: center;">🏆 Career Achievements</h5>',
        '<div style="display: flex; flex-wrap: wrap; gap: 0.75rem; justify-content: center; width: 100%;">'
    ]
    
    for b in badges:
        opacity = "1" if b["unlocked"] else "0.35"
        shadow = f"0 2px 8px {b['border']}30" if b["unlocked"] else "none"
        text_style = "color: #ffffff; font-weight: 600;" if b["unlocked"] else "color: #8892b0; text-decoration: line-through; opacity: 0.7;"
        bg_style = f"background: {b['color']}; border: 1px solid {b['border']};"
        
        html_lines.append(f"""
        <div style="display: flex; align-items: center; gap: 0.6rem; padding: 0.4rem 0.8rem; border-radius: 8px; {bg_style} box-shadow: {shadow}; opacity: {opacity}; transition: all 0.3s ease;">
            <span style="font-size: 1.1rem;">{b['emoji']}</span>
            <span style="font-size: 0.85rem; {text_style}">{b['label']}</span>
        </div>
        """)
        
    html_lines.append('</div></div>')
    return "".join(html_lines).replace("\n", "").replace("\r", "").strip()


# ── Main page layout ───────────────────────────────────────────────

def main() -> None:
    """Orchestrate the entire Player Analytics page."""

    # ── Sidebar Branding ──
    with st.sidebar:
        st.markdown("### 🏏 IPLytics")
        st.caption("Player Analytics")
        st.divider()

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
    default_index = 0
    if "V Kohli" in players:
        default_index = players.index("V Kohli")

    selected_player = st.selectbox(
        "Select a Player",
        options=players,
        index=default_index,
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
    season_wickets: list[dict] = stats.get("season_wickets", [])

    has_batted = batting.get("matches", 0) > 0
    has_bowled = bowling.get("matches", 0) > 0

    # ── Fetch Cap Winners ──
    leaders_data = load_ipl_leaders()
    orange_seasons = []
    purple_seasons = []
    if leaders_data:
        caps_dict = leaders_data.get("caps", {})
        for cap in caps_dict.get("orange", []):
            if cap.get("player") == selected_player:
                orange_seasons.append(str(cap.get("season")))
        for cap in caps_dict.get("purple", []):
            if cap.get("player") == selected_player:
                purple_seasons.append(str(cap.get("season")))

    # ── Sidebar Dynamic Profile & suggestions ──
    with st.sidebar:
        # Determine player role dynamically using career stats and stumping records
        is_wk = stats.get("is_wicketkeeper", False)
        runs = batting.get("total_runs", 0) or 0
        wickets = bowling.get("wickets", 0) or 0
        
        if is_wk:
            role = "🧤 Wicket-Keeper Batsman"
        elif runs >= 500 and wickets >= 15 and runs <= wickets * 120:
            role = "🏏 All-Rounder"
        elif wickets >= 10 or (wickets >= 1 and runs < 100):
            role = "🎳 Bowler"
        else:
            role = "🏏 Batsman"
            
        abbrev_map = {
            "Chennai Super Kings": "CSK",
            "Mumbai Indians": "MI",
            "Royal Challengers Bengaluru": "RCB",
            "Royal Challengers Bangalore": "RCB",
            "Kolkata Knight Riders": "KKR",
            "Sunrisers Hyderabad": "SRH",
            "Delhi Capitals": "DC",
            "Delhi Daredevils": "DD",
            "Rajasthan Royals": "RR",
            "Punjab Kings": "PBKS",
            "Kings XI Punjab": "KXIP",
            "Gujarat Titans": "GT",
            "Lucknow Super Giants": "LSG",
            "Deccan Chargers": "DCG",
            "Kochi Tuskers Kerala": "KTK",
            "Pune Warriors": "PWI",
            "Rising Pune Supergiant": "RPS",
            "Rising Pune Supergiants": "RPS",
            "Gujarat Lions": "GL"
        }
        short_teams = [abbrev_map.get(t, t) for t in player_teams]
        
        st.markdown("#### 👤 Player Profile Summary")
        st.markdown(f"""
        <div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(233, 69, 96, 0.15); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h5 style="margin: 0 0 0.5rem 0; color: #f5a623; font-size: 1.1rem; font-weight: 700;">{selected_player}</h5>
            <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">🎭 Role: <strong>{role}</strong></div>
            <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">🏟️ Teams: <strong>{", ".join(short_teams[:3]) if short_teams else "None"}</strong></div>
            <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">🏏 Career Runs: <strong>{batting.get("total_runs", 0):,}</strong></div>
            <div style="font-size: 0.9rem; color: #ccd6f6;">🎳 Career Wkts: <strong>{bowling.get("wickets", 0)}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        

        

    # ── Metric cards ──
    render_batting_metrics(batting)
    st.divider()
    render_bowling_metrics(bowling)
    st.divider()

    # ── Charts side-by-side ──
    col_season_runs, col_season_wkts = st.columns(2)

    with col_season_runs:
        render_season_runs_chart(season_runs, selected_player, has_batted)

    with col_season_wkts:
        render_season_wickets_chart(season_wickets, selected_player, has_bowled)

    st.divider()
    render_consistency_charts(batting, bowling, selected_player)

    # Render visual achievements cabinet
    cabinet_html = generate_trophy_cabinet_html(batting, bowling, orange_seasons, purple_seasons)
    st.markdown(cabinet_html, unsafe_allow_html=True)


main()
