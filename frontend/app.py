"""
IPLytics Frontend — Home Dashboard

WHY THIS FILE EXISTS:
    This is the main entry point for the Streamlit frontend.
    It shows an overview dashboard with key IPL statistics
    and serves as the navigation hub for all analytics pages.

HOW TO RUN:
    Start the backend first:
        uvicorn backend.app.main:app --reload

    Then run the frontend:
        streamlit run frontend/app.py
"""

import sys
from pathlib import Path

# Add project root to Python path so 'frontend' is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from frontend.api_client import check_health, get_players, get_teams, get_venues


# --- Page Configuration (must be first!) ---
st.set_page_config(
    page_title="IPLytics — AI-Powered IPL Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for premium styling ---
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* Hero title styling */
    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #e94560, #f5a623);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
        padding-top: 1rem;
    }

    .hero-subtitle {
        font-size: 1.2rem;
        color: #8892b0;
        text-align: center;
        margin-top: 0;
        margin-bottom: 2rem;
    }

    /* Metric card styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #e9456030;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.1);
    }

    div[data-testid="stMetric"] label {
        color: #8892b0 !important;
        font-size: 0.85rem;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #e94560 !important;
        font-size: 2rem;
        font-weight: 700;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23, #1a1a2e);
        border-right: 1px solid #e9456020;
    }

    /* Feature card styling */
    .feature-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #e9456020;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        border-color: #e94560;
        box-shadow: 0 4px 20px rgba(233, 69, 96, 0.2);
    }

    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    .feature-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #ccd6f6;
        margin-bottom: 0.3rem;
    }

    .feature-desc {
        font-size: 0.85rem;
        color: #8892b0;
    }

    /* Divider */
    hr {
        border-color: #e9456020 !important;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .status-online {
        background: #10b98120;
        color: #10b981;
        border: 1px solid #10b98140;
    }

    .status-offline {
        background: #ef444420;
        color: #ef4444;
        border: 1px solid #ef444440;
    }
</style>
""", unsafe_allow_html=True)


def main() -> None:
    """Render the IPLytics home dashboard."""

    # --- Hero Header ---
    st.markdown('<h1 class="hero-title">🏏 IPLytics</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-subtitle">AI-Powered IPL Analytics Platform • 2008–2025</p>',
        unsafe_allow_html=True,
    )

    # --- Backend Status Check ---
    backend_online = check_health()

    # --- Overview Stats ---
    if backend_online:
        players = get_players()
        teams = get_teams()
        venues = get_venues()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Matches", "1,212")
        with col2:
            st.metric("Players", f"{len(players):,}")
        with col3:
            st.metric("Teams", f"{len(teams)}")
        with col4:
            st.metric("Venues", f"{len(venues)}")

    st.divider()

    # --- Feature Cards ---
    st.markdown("### 📊 Explore Analytics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🏏</div>
            <div class="feature-name">Player Analytics</div>
            <div class="feature-desc">Batting & bowling stats, season trends, milestones</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🏆</div>
            <div class="feature-name">Team Analytics</div>
            <div class="feature-desc">Win records, season performance, toss analysis</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🏟️</div>
            <div class="feature-name">Venue Analytics</div>
            <div class="feature-desc">Scoring patterns, chase success rates, pitch trends</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚔️</div>
            <div class="feature-name">Comparisons</div>
            <div class="feature-desc">Player vs Player, Team vs Team, Head-to-Head</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- Quick Info ---
    st.markdown("### 🔥 Quick Facts")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("📅 **18 Seasons** of IPL data (2008–2025)")
    with col2:
        st.info("📦 **288,226** ball-by-ball deliveries analyzed")
    with col3:
        st.info("🤖 **AI-powered** insights coming soon!")

    # --- Sidebar ---
    with st.sidebar:
        st.markdown("### 🏏 IPLytics")
        st.caption("v1.0.0 • AI-Powered IPL Analytics")
        st.divider()

        # Backend status
        if backend_online:
            st.markdown(
                '<span class="status-badge status-online">● Backend Online</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="status-badge status-offline">● Backend Offline</span>',
                unsafe_allow_html=True,
            )
            st.warning("Start the backend: `uvicorn backend.app.main:app --reload`")

        st.divider()
        st.markdown("#### 📌 Navigation")
        st.markdown("""
        Use the sidebar to navigate to:
        - 🏏 Player Analytics
        - 🏆 Team Analytics
        - 🏟️ Venue Analytics
        - ⚔️ Comparisons
        """)

        st.divider()
        st.caption("Built with ❤️ using FastAPI + Streamlit + PostgreSQL")


if __name__ == "__main__":
    main()
