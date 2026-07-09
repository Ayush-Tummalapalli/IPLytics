"""
IPLytics Frontend — Team Analytics Page

Displays comprehensive team statistics, season-wise performance trends,
and win/loss breakdowns with interactive Plotly charts.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go

from frontend.api_client import get_teams, get_team_stats, get_ipl_champions

# --- Page Config ---
st.set_page_config(
    page_title="Team Analytics | IPLytics",
    page_icon="🏆",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp, * {
        font-family: 'Outfit', sans-serif !important;
    }
    .stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #e9456030; border-radius: 12px; padding: 1rem;
        transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease, border-color 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #e9456080;
        box-shadow: 0 12px 30px rgba(233, 69, 96, 0.25);
    }
    div[data-testid="stMetric"] label { color: #8892b0 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e94560 !important; font-weight: 700;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23, #1a1a2e);
    }
    [data-testid="stSidebarNavItems"] {
        max-height: none !important;
    }
</style>
""", unsafe_allow_html=True)

TEAM_COLORS = {
    "Chennai Super Kings": {"bg": "linear-gradient(135deg, #FFF9C4 0%, #FBC02D 100%)", "border": "#FFD700", "text": "#002F6C", "glow": "rgba(255, 215, 0, 0.4)"},
    "Mumbai Indians": {"bg": "linear-gradient(135deg, #1A237E 0%, #0D47A1 100%)", "border": "#00D4FF", "text": "#FFFFFF", "glow": "rgba(0, 212, 255, 0.3)"},
    "Royal Challengers Bengaluru": {"bg": "linear-gradient(135deg, #1A1A1A 0%, #2D0000 100%)", "border": "#E94560", "text": "#FFFFFF", "glow": "rgba(233, 69, 96, 0.4)"},
    "Royal Challengers Bangalore": {"bg": "linear-gradient(135deg, #1A1A1A 0%, #2D0000 100%)", "border": "#E94560", "text": "#FFFFFF", "glow": "rgba(233, 69, 96, 0.4)"},
    "Kolkata Knight Riders": {"bg": "linear-gradient(135deg, #311B92 0%, #1A237E 100%)", "border": "#FFD700", "text": "#FFFFFF", "glow": "rgba(255, 215, 0, 0.3)"},
    "Sunrisers Hyderabad": {"bg": "linear-gradient(135deg, #FF6F00 0%, #E65100 100%)", "border": "#000000", "text": "#FFFFFF", "glow": "rgba(255, 111, 0, 0.4)"},
    "Delhi Capitals": {"bg": "linear-gradient(135deg, #0D47A1 0%, #D50000 100%)", "border": "#FFFFFF", "text": "#FFFFFF", "glow": "rgba(255, 255, 255, 0.3)"},
    "Delhi Daredevils": {"bg": "linear-gradient(135deg, #0D47A1 0%, #D50000 100%)", "border": "#FFFFFF", "text": "#FFFFFF", "glow": "rgba(255, 255, 255, 0.3)"},
    "Rajasthan Royals": {"bg": "linear-gradient(135deg, #C2185B 0%, #0D47A1 100%)", "border": "#00D4FF", "text": "#FFFFFF", "glow": "rgba(0, 212, 255, 0.4)"},
    "Punjab Kings": {"bg": "linear-gradient(135deg, #D50000 0%, #B71C1C 100%)", "border": "#FFD700", "text": "#FFFFFF", "glow": "rgba(255, 215, 0, 0.4)"},
    "Kings XI Punjab": {"bg": "linear-gradient(135deg, #D50000 0%, #B71C1C 100%)", "border": "#FFD700", "text": "#FFFFFF", "glow": "rgba(255, 215, 0, 0.4)"},
    "Gujarat Titans": {"bg": "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)", "border": "#D4AF37", "text": "#FFFFFF", "glow": "rgba(212, 175, 55, 0.3)"},
    "Lucknow Super Giants": {"bg": "linear-gradient(135deg, #E0F7FA 0%, #80DEEA 100%)", "border": "#FFB300", "text": "#0D47A1", "glow": "rgba(255, 179, 0, 0.4)"},
    "Deccan Chargers": {"bg": "linear-gradient(135deg, #263238 0%, #37474F 100%)", "border": "#CFD8DC", "text": "#FFFFFF", "glow": "rgba(207, 216, 220, 0.3)"},
    "Kochi Tuskers Kerala": {"bg": "linear-gradient(135deg, #FF6F00 0%, #7B1FA2 100%)", "border": "#FFFFFF", "text": "#FFFFFF", "glow": "rgba(255, 255, 255, 0.3)"},
    "Pune Warriors": {"bg": "linear-gradient(135deg, #37474F 0%, #455A64 100%)", "border": "#00E5FF", "text": "#FFFFFF", "glow": "rgba(0, 229, 255, 0.3)"},
    "Rising Pune Supergiant": {"bg": "linear-gradient(135deg, #8E24AA 0%, #D81B60 100%)", "border": "#FFD700", "text": "#FFFFFF", "glow": "rgba(255, 215, 0, 0.3)"},
    "Rising Pune Supergiants": {"bg": "linear-gradient(135deg, #8E24AA 0%, #D81B60 100%)", "border": "#FFD700", "text": "#FFFFFF", "glow": "rgba(255, 215, 0, 0.3)"},
    "Gujarat Lions": {"bg": "linear-gradient(135deg, #FF6F00 0%, #FFB300 100%)", "border": "#D50000", "text": "#D50000", "glow": "rgba(213, 0, 0, 0.3)"},
}

COLOR_PRIMARY = "#e94560"
COLOR_SECONDARY = "#0f3460"
COLOR_GOLD = "#f5a623"

with st.sidebar:
    st.markdown("### 🏏 IPLytics")
    st.caption("Team Analytics")
    st.divider()


@st.cache_data(ttl=300)
def fetch_teams():
    return get_teams()


@st.cache_data(ttl=300)
def fetch_team_stats(name):
    return get_team_stats(name)


@st.cache_data(ttl=600)
def fetch_champions():
    return get_ipl_champions()


def render_championships_glory_panel(titles: list[dict], team_name: str) -> None:
    """Render a horizontal timeline panel of championship final details."""
    if not titles:
        return
        
    st.markdown("### 🏆 Championship Glory Timeline")
    
    # Captain map
    WINNING_CAPTAINS = {
        2008: "Shane Warne",
        2009: "Adam Gilchrist",
        2010: "MS Dhoni",
        2011: "MS Dhoni",
        2012: "Gautam Gambhir",
        2013: "Rohit Sharma",
        2014: "Gautam Gambhir",
        2015: "Rohit Sharma",
        2016: "David Warner",
        2017: "Rohit Sharma",
        2018: "MS Dhoni",
        2019: "Rohit Sharma",
        2020: "Rohit Sharma",
        2021: "MS Dhoni",
        2022: "Hardik Pandya",
        2023: "MS Dhoni",
        2024: "Shreyas Iyer",
        2025: "Rajat Patidar"
    }

    html_lines = [
        '<div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; width: 100%;">'
    ]
    
    for t in sorted(titles, key=lambda x: x["season"]):
        season = t["season"]
        captain = WINNING_CAPTAINS.get(season, "Unknown Captain")
        opponent = t.get("opponent", "Opponent")
        margin = t.get("margin", "won")
        pom = t.get("player_of_match", "N/A")
        
        html_lines.append(f"""
        <div style="flex: 1 1 280px; min-width: 250px; background: linear-gradient(135deg, #1a1a2e 0%, #2a2010 100%); border: 1px solid rgba(245, 166, 35, 0.35); border-radius: 12px; padding: 1.25rem; box-shadow: 0 4px 15px rgba(245, 166, 35, 0.15); transition: transform 0.3s ease;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <span style="font-size: 1.5rem; font-weight: 800; color: #f5a623;">🏆 {season}</span>
                <span style="font-size: 0.75rem; background: rgba(245, 166, 35, 0.15); color: #f5a623; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: bold;">CHAMPIONS</span>
            </div>
            <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">👨‍✈️ Captain: <strong style="color: #ffffff;">{captain}</strong></div>
            <div style="font-size: 0.88rem; color: #ccd6f6; margin-bottom: 0.4rem;">⚔️ Final: {margin} vs <strong>{opponent}</strong></div>
            <div style="font-size: 0.85rem; color: #8892b0;">🌟 Final POM: <strong style="color: #ccd6f6;">{pom}</strong></div>
        </div>
        """)
        
    html_lines.append("</div>")
    st.markdown("".join(html_lines).replace("\n", "").replace("\r", "").strip(), unsafe_allow_html=True)
    st.divider()


def render_home_away_split(home_away: dict, team_name: str) -> None:
    """Render a side-by-side dashboard comparing home vs away performance."""
    if not home_away:
        return
        
    home = home_away.get("home", {"matches": 0, "wins": 0, "losses": 0, "win_pct": 0.0})
    away = home_away.get("away", {"matches": 0, "wins": 0, "losses": 0, "win_pct": 0.0})
    
    st.markdown("### 🏟️ Home vs Away Performance Split")
    st.caption("Comparison of historical win ratios at home venue vs all away and neutral grounds.")
    
    col_home, col_away = st.columns(2)
    
    with col_home:
        html_h = f"""
        <div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(245, 166, 35, 0.2); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.05rem; font-weight: bold; color: #f5a623;">🏠 Home Venue Performance</span>
                <span style="font-size: 1.3rem; font-weight: bold; color: #f5a623;">{home['win_pct']}% Win</span>
            </div>
            <div style="font-size: 0.9rem; color: #ccd6f6;">Matches Played: <strong>{home['matches']}</strong></div>
            <div style="font-size: 0.9rem; color: #ccd6f6;">Wins: <strong>{home['wins']}</strong> | Losses: <strong>{home['losses']}</strong></div>
            <div style="background: rgba(255,255,255,0.05); height: 8px; border-radius: 4px; overflow: hidden; margin-top: 0.25rem;">
                <div style="background: #f5a623; width: {home['win_pct']}%; height: 100%;"></div>
            </div>
        </div>
        """
        st.markdown(html_h.replace("\n", "").strip(), unsafe_allow_html=True)
        
    with col_away:
        html_a = f"""
        <div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(233, 69, 96, 0.2); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.05rem; font-weight: bold; color: #e94560;">✈️ Away / Neutral Performance</span>
                <span style="font-size: 1.3rem; font-weight: bold; color: #e94560;">{away['win_pct']}% Win</span>
            </div>
            <div style="font-size: 0.9rem; color: #ccd6f6;">Matches Played: <strong>{away['matches']}</strong></div>
            <div style="font-size: 0.9rem; color: #ccd6f6;">Wins: <strong>{away['wins']}</strong> | Losses: <strong>{away['losses']}</strong></div>
            <div style="background: rgba(255,255,255,0.05); height: 8px; border-radius: 4px; overflow: hidden; margin-top: 0.25rem;">
                <div style="background: #e94560; width: {away['win_pct']}%; height: 100%;"></div>
            </div>
        </div>
        """
        st.markdown(html_a.replace("\n", "").strip(), unsafe_allow_html=True)
    st.write("")


def render_opponents_breakdown(opponents: list[dict], team_name: str) -> None:
    """Render stacked horizontal bar chart against all opponents."""
    if not opponents:
        return
        
    st.markdown("### ⚔️ Opponents Head-to-Head Win/Loss Breakdown")
    st.caption("Historical win ratio details against all opponent franchises (ordered by matches played).")
    
    opp_labels = [o["short_name"] for o in opponents]
    opp_full_names = [o["opponent"] for o in opponents]
    wins = [o["wins"] for o in opponents]
    losses = [o["losses"] for o in opponents]
    no_results = [o["no_results"] for o in opponents]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=opp_labels,
        x=wins,
        name="Wins",
        orientation="h",
        marker_color="#f5a623",
        hovertemplate="vs %{customdata}: %{x} Wins<extra></extra>",
        customdata=opp_full_names
    ))
    fig.add_trace(go.Bar(
        y=opp_labels,
        x=losses,
        name="Losses",
        orientation="h",
        marker_color="#e94560",
        hovertemplate="vs %{customdata}: %{x} Losses<extra></extra>",
        customdata=opp_full_names
    ))
    fig.add_trace(go.Bar(
        y=opp_labels,
        x=no_results,
        name="No Results / Ties",
        orientation="h",
        marker_color="rgba(255, 255, 255, 0.2)",
        hovertemplate="vs %{customdata}: %{x} No Results<extra></extra>",
        customdata=opp_full_names
    ))
    
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        barmode="stack",
        height=max(350, len(opponents) * 35),
        margin=dict(t=20, b=40, l=60, r=20),
        font=dict(color="#8892b0"),
        legend=dict(font=dict(color="#ccd6f6")),
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig, use_container_width=True)


# --- Main Content ---
st.title("🏆 Team Analytics")
st.markdown("Explore team performance, win records, and season trends (2008–2025)")

teams = fetch_teams()
if not teams:
    st.error("⚠️ Could not load teams. Is the backend running?")
    st.stop()

team_names = [t["name"] for t in teams]
team_display = [f"{t['short_name']} — {t['name']}" for t in teams]

selected_idx = st.selectbox(
    "Select a Team",
    range(len(teams)),
    format_func=lambda i: team_display[i],
    index=team_names.index("Mumbai Indians") if "Mumbai Indians" in team_names else 0,
)
selected_team = team_names[selected_idx]

# Inject dynamic team branding colors
colors = TEAM_COLORS.get(selected_team, {"bg": "linear-gradient(135deg, #1a1a2e, #16213e)", "border": "#e9456030", "text": "#e94560", "glow": "rgba(233, 69, 96, 0.1)"})
st.markdown(f"""
<style>
    div[data-testid="stMetric"] {{
        background: {colors['bg']} !important;
        border: 1px solid {colors['border']}80 !important;
        box-shadow: 0 4px 15px {colors['glow']} !important;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-5px);
        border-color: {colors['border']} !important;
        box-shadow: 0 12px 30px {colors['glow']} !important;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        color: {colors['text']} !important;
    }}
</style>
""", unsafe_allow_html=True)

data = fetch_team_stats(selected_team)
if not data:
    st.warning(f"No data found for '{selected_team}'")
    st.stop()

stats = data["stats"]
season_perf = data["season_performance"]
home_away = data.get("home_away", {})
opponents = data.get("opponents", [])

# ── Sidebar dynamic profile card ──
with st.sidebar:
    championships = {
        "Chennai Super Kings": 5, "Mumbai Indians": 5, "Kolkata Knight Riders": 3,
        "Rajasthan Royals": 1, "Deccan Chargers": 1, "Sunrisers Hyderabad": 1,
        "Gujarat Titans": 1, "Royal Challengers Bengaluru": 1, "Royal Challengers Bangalore": 1
    }
    titles = championships.get(selected_team, 0)
    titles_str = f"🏆 {titles} Titles" if titles > 0 else "❌ No Titles"
    
    home_grounds = {
        "Chennai Super Kings": "MA Chidambaram Stadium",
        "Mumbai Indians": "Wankhede Stadium",
        "Royal Challengers Bengaluru": "M Chinnaswamy Stadium",
        "Royal Challengers Bangalore": "M Chinnaswamy Stadium",
        "Kolkata Knight Riders": "Eden Gardens",
        "Sunrisers Hyderabad": "Rajiv Gandhi Stadium",
        "Delhi Capitals": "Arun Jaitley Stadium",
        "Delhi Daredevils": "Feroz Shah Kotla",
        "Rajasthan Royals": "Sawai Mansingh Stadium",
        "Punjab Kings": "IS Bindra Stadium",
        "Kings XI Punjab": "IS Bindra Stadium",
        "Gujarat Titans": "Narendra Modi Stadium",
        "Lucknow Super Giants": "BRSABV Ekana Stadium"
    }
    home = home_grounds.get(selected_team, "Multiple / Neutral Venues")
    
    st.markdown("#### 🏆 Franchise Profile Summary")
    st.markdown(f"""
    <div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(233, 69, 96, 0.15); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        <h5 style="margin: 0 0 0.5rem 0; color: #f5a623; font-size: 1.1rem; font-weight: 700;">{selected_team}</h5>
        <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">🏅 Titles: <strong>{titles_str}</strong></div>
        <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">🏟️ Home Ground: <strong>{home}</strong></div>
        <div style="font-size: 0.9rem; color: #ccd6f6;">📈 Win %: <strong>{stats['win_percentage']}%</strong></div>
    </div>
    """, unsafe_allow_html=True)



st.divider()

# =============================================
# OVERVIEW STATS
# =============================================
st.markdown(f"### 📊 {stats['name']} ({stats['short_name']})")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Matches", f"{stats['total_matches']}")
with col2:
    st.metric("Wins", f"{stats['wins']}")
with col3:
    st.metric("Losses", f"{stats['losses']}")
with col4:
    st.metric("Win %", f"{stats['win_percentage']}%")
with col5:
    st.metric("Toss Wins", f"{stats['toss_wins']}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Bat First Wins", f"{stats['bat_first_wins']}")
with col2:
    st.metric("Chase Wins", f"{stats['field_first_wins']}")
with col3:
    no_res = stats.get("no_results", 0)
    st.metric("No Results", f"{no_res}")

st.divider()

# --- Dynamic Championship Glory Panel ---
champions_list = fetch_champions()
team_titles = []
if champions_list:
    for champ in champions_list:
        if champ.get("champion") == selected_team:
            team_titles.append(champ)

if team_titles:
    render_championships_glory_panel(team_titles, selected_team)

# --- Home vs Away Performance Split ---
render_home_away_split(home_away, selected_team)

st.divider()

# =============================================
# CHARTS
# =============================================
chart_col1, chart_col2 = st.columns(2)

# --- Win Percentage Trend ---
with chart_col1:
    st.markdown("#### 📈 Season Win Percentage")
    if season_perf:
        seasons = [str(s["season"]) for s in season_perf]
        win_pcts = [s["win_percentage"] for s in season_perf]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=seasons, y=win_pcts,
            mode="lines+markers+text",
            line=dict(color=COLOR_PRIMARY, width=3),
            marker=dict(size=8, color=COLOR_PRIMARY),
            text=[f"{w:.0f}%" for w in win_pcts],
            textposition="top center",
            textfont=dict(color="#ccd6f6", size=10),
        ))

        fig.add_hline(y=50, line_dash="dash", line_color="rgba(136,146,176,0.25)",
                      annotation_text="50%", annotation_font_color="#8892b0")

        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Season", yaxis_title="Win %",
            yaxis=dict(range=[0, 100]),
            height=400, margin=dict(t=20, b=40),
            font=dict(color="#8892b0"),
        )
        st.plotly_chart(fig, use_container_width=True)

# --- Wins vs Losses Per Season ---
with chart_col2:
    st.markdown("#### 🏆 Wins vs Losses by Season")
    if season_perf:
        seasons = [str(s["season"]) for s in season_perf]
        wins = [s["wins"] for s in season_perf]
        losses = [s["losses"] for s in season_perf]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=seasons, y=wins, name="Wins",
            marker_color=COLOR_PRIMARY,
        ))
        fig.add_trace(go.Bar(
            x=seasons, y=losses, name="Losses",
            marker_color=COLOR_SECONDARY,
        ))

        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            barmode="group",
            xaxis_title="Season",
            yaxis_title="Matches",
            height=400, margin=dict(t=20, b=40),
            font=dict(color="#8892b0"),
            legend=dict(font=dict(color="#ccd6f6")),
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Win Method Donut Chart ---
st.markdown("#### 🎯 Win Method Breakdown")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    bat_wins = stats["bat_first_wins"]
    chase_wins = stats["field_first_wins"]

    fig = go.Figure(data=[go.Pie(
        labels=["Bat First Wins", "Chase Wins"],
        values=[bat_wins, chase_wins],
        hole=0.5,
        marker_colors=[COLOR_PRIMARY, COLOR_GOLD],
        textfont=dict(color="#ccd6f6", size=14),
        textinfo="label+value",
    )])
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin=dict(t=20, b=20),
        font=dict(color="#8892b0"),
        legend=dict(font=dict(color="#ccd6f6")),
        annotations=[dict(
            text=f"{stats['wins']} Wins",
            x=0.5, y=0.5, font_size=18,
            font_color=COLOR_PRIMARY,
            showarrow=False,
        )],
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Opponents Head-to-Head Breakdown ---
render_opponents_breakdown(opponents, selected_team)
