"""
IPLytics Frontend — Venue Analytics Page

Displays venue-specific statistics including average scores,
chase success rates, and scoring patterns.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go

from frontend.api_client import get_venues, get_venue_stats

# --- Page Config ---
st.set_page_config(
    page_title="Venue Analytics | IPLytics",
    page_icon="🏟️",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #e9456030; border-radius: 12px; padding: 1rem;
    }
    div[data-testid="stMetric"] label { color: #8892b0 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e94560 !important; font-weight: 700;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23, #1a1a2e);
    }
</style>
""", unsafe_allow_html=True)

COLOR_PRIMARY = "#e94560"
COLOR_SECONDARY = "#0f3460"
COLOR_GOLD = "#f5a623"

with st.sidebar:
    st.markdown("### 🏏 IPLytics")
    st.caption("Venue Analytics")
    st.divider()


@st.cache_data(ttl=300)
def fetch_venues():
    return get_venues()


@st.cache_data(ttl=300)
def fetch_venue_stats(name):
    return get_venue_stats(name)


# --- Main Content ---
st.title("🏟️ Venue Analytics")
st.markdown("Explore scoring patterns, chase success rates, and pitch behavior at IPL venues")

venues = fetch_venues()
if not venues:
    st.error("⚠️ Could not load venues. Is the backend running?")
    st.stop()

selected = st.selectbox(
    "Select a Venue",
    options=venues,
    index=venues.index("M Chinnaswamy Stadium") if "M Chinnaswamy Stadium" in venues else 0,
    placeholder="Search for a venue...",
)

if selected:
    data = fetch_venue_stats(selected)

    if not data:
        st.warning(f"No data found for '{selected}'")
        st.stop()

    stats = data["stats"]

    st.divider()

    # =============================================
    # VENUE HEADER
    # =============================================
    st.markdown(f"### 📍 {stats['venue']}")
    st.caption(f"📌 {stats['city']}")

    # =============================================
    # OVERVIEW STATS
    # =============================================
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Matches", f"{stats['total_matches']}")
    with col2:
        st.metric("Avg 1st Innings", f"{stats['avg_first_innings_score']}")
    with col3:
        st.metric("Avg 2nd Innings", f"{stats['avg_second_innings_score']}")
    with col4:
        st.metric("Highest Total", f"{stats['highest_total']}")
    with col5:
        st.metric("Lowest Total", f"{stats['lowest_total']}")

    st.divider()

    # =============================================
    # CHARTS
    # =============================================
    chart_col1, chart_col2 = st.columns(2)

    # --- 1st vs 2nd Innings Average ---
    with chart_col1:
        st.markdown("#### 📊 Average Innings Scores")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["1st Innings", "2nd Innings"],
            y=[stats["avg_first_innings_score"], stats["avg_second_innings_score"]],
            marker_color=[COLOR_PRIMARY, COLOR_SECONDARY],
            text=[f"{stats['avg_first_innings_score']}", f"{stats['avg_second_innings_score']}"],
            textposition="outside",
            textfont=dict(color="#ccd6f6", size=16),
            width=0.5,
        ))

        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Avg Score",
            height=400, margin=dict(t=20, b=40),
            font=dict(color="#8892b0"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Chase Success Donut ---
    with chart_col2:
        st.markdown("#### 🎯 Bat First vs Chase")

        chase_rate = stats["chase_success_rate"]
        bat_rate = stats["bat_first_win_pct"]

        fig = go.Figure(data=[go.Pie(
            labels=["Chase Wins", "Bat First Wins"],
            values=[chase_rate, bat_rate],
            hole=0.55,
            marker_colors=[COLOR_GOLD, COLOR_PRIMARY],
            textfont=dict(color="#ccd6f6", size=13),
            textinfo="label+percent",
        )])

        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=400,
            margin=dict(t=20, b=20),
            font=dict(color="#8892b0"),
            legend=dict(font=dict(color="#ccd6f6")),
            annotations=[dict(
                text=f"Chase<br>{chase_rate}%",
                x=0.5, y=0.5, font_size=16,
                font_color=COLOR_GOLD,
                showarrow=False,
            )],
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- Score Range Indicators ---
    st.markdown("#### 📈 Scoring Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Score (All)", f"{stats['avg_score']}")
    with col2:
        score_diff = round(stats["avg_first_innings_score"] - stats["avg_second_innings_score"], 1)
        label = "1st Innings Advantage" if score_diff > 0 else "2nd Innings Advantage"
        st.metric(label, f"{abs(score_diff)} runs")
    with col3:
        range_val = stats["highest_total"] - stats["lowest_total"]
        st.metric("Score Range", f"{range_val} runs")
