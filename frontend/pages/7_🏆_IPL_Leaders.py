"""
IPLytics Frontend — IPL Leaderboards & Stats Page

Displays Orange and Purple Cap histories alongside top 10 career leaderboards
using tables and Plotly bar charts.
"""

import sys
from pathlib import Path

# Add project root to Python path so 'frontend' is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px

from frontend.api_client import get_ipl_leaders

# --- Page Config ---
st.set_page_config(
    page_title="IPL Leaderboards & Caps | IPLytics",
    page_icon="🏆",
    layout="wide",
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23, #1a1a2e);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Branding
with st.sidebar:
    st.markdown("### 🏆 IPL Leaderboards")
    st.caption("All-time Caps & Career Top 10s")
    st.divider()
    st.markdown(
        "Explore historical season cap winners and all-time top 10 player "
        "rankings calculated dynamically from our database (2008–2025)."
    )
    st.divider()
    st.info("💡 Note: Averages require a minimum of 20 career innings or 20 wickets taken to filter out outliers.")

# Page Header
st.title("🏆 IPL Leaderboards & Caps")
st.markdown(
    "<p style='color: #8892b0; font-size: 1.15rem; margin-top: -0.5rem;'>"
    "View Orange Cap, Purple Cap winners history, and career top 10 statistics."
    "</p>",
    unsafe_allow_html=True
)
st.divider()

# Fetch leaderboards from API
with st.spinner("Calculating leaderboard statistics..."):
    data = get_ipl_leaders()

if not data:
    st.error("Could not fetch leaderboards from the database. Please make sure the backend is running.")
    st.stop()

caps = data.get("caps", {})
leaders = data.get("leaderboards", {})

# Tabs layout
tab_caps, tab_batting, tab_bowling = st.tabs([
    "🥇 Season Caps",
    "🏏 Batting Leaders",
    "🥎 Bowling Leaders"
])

with tab_caps:
    st.subheader("Historical Orange & Purple Cap Winners")
    st.markdown("The Orange Cap is awarded to the top run-scorer, and the Purple Cap is awarded to the top wicket-taker of each season.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h4 style='color: #f5a623;'>🟠 Orange Cap History (2008–2025)</h4>", unsafe_allow_html=True)
        orange_list = caps.get("orange", [])
        if orange_list:
            df_orange = pd.DataFrame(orange_list)
            df_orange.columns = ["Season", "Player", "Runs Scored"]
            
            # Format and display
            st.dataframe(
                df_orange,
                column_config={
                    "Season": st.column_config.NumberColumn(format="%d"),
                    "Player": st.column_config.TextColumn(),
                    "Runs Scored": st.column_config.NumberColumn(format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No Orange Cap data available.")

    with col2:
        st.markdown("<h4 style='color: #b085f5;'>🟣 Purple Cap History (2008–2025)</h4>", unsafe_allow_html=True)
        purple_list = caps.get("purple", [])
        if purple_list:
            df_purple = pd.DataFrame(purple_list)
            df_purple.columns = ["Season", "Player", "Wickets Taken"]
            
            # Format and display
            st.dataframe(
                df_purple,
                column_config={
                    "Season": st.column_config.NumberColumn(format="%d"),
                    "Player": st.column_config.TextColumn(),
                    "Wickets Taken": st.column_config.NumberColumn(format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No Purple Cap data available.")

with tab_batting:
    st.subheader("All-Time Batting Leaderboards")
    
    # 1. Most Runs & Sixes side-by-side with charts
    col_runs, col_sixes = st.columns(2)
    
    with col_runs:
        st.markdown("<h4 style='color: #00bcd4;'>📈 Top 10 Career Runs</h4>", unsafe_allow_html=True)
        runs_list = leaders.get("runs", [])
        if runs_list:
            df_runs = pd.DataFrame(runs_list)
            df_runs.columns = ["Rank", "Player", "Runs"]
            
            fig = px.bar(
                df_runs,
                x="Runs",
                y="Player",
                orientation="h",
                text="Runs",
                color="Runs",
                color_continuous_scale="Viridis",
                category_orders={"Player": df_runs["Player"].tolist()[::-1]}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                showlegend=False,
                coloraxis_showscale=False,
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df_runs, hide_index=True, use_container_width=True)

    with col_sixes:
        st.markdown("<h4 style='color: #e94560;'>💥 Top 10 Career Sixes</h4>", unsafe_allow_html=True)
        sixes_list = leaders.get("sixes", [])
        if sixes_list:
            df_sixes = pd.DataFrame(sixes_list)
            df_sixes.columns = ["Rank", "Player", "Sixes"]
            
            fig = px.bar(
                df_sixes,
                x="Sixes",
                y="Player",
                orientation="h",
                text="Sixes",
                color="Sixes",
                color_continuous_scale="Magma",
                category_orders={"Player": df_sixes["Player"].tolist()[::-1]}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                showlegend=False,
                coloraxis_showscale=False,
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df_sixes, hide_index=True, use_container_width=True)
            
    st.divider()
    
    # 2. Batting average
    st.markdown("<h4 style='color: #00bcd4;'>🔥 Top 10 Batting Average (Min. 20 Innings)</h4>", unsafe_allow_html=True)
    avg_list = leaders.get("batting_average", [])
    if avg_list:
        df_avg = pd.DataFrame(avg_list)
        df_avg.columns = ["Rank", "Player", "Total Runs", "Dismissals", "Average"]
        st.dataframe(
            df_avg,
            column_config={
                "Average": st.column_config.NumberColumn(format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )

with tab_bowling:
    st.subheader("All-Time Bowling Leaderboards")
    
    col_wkts, col_bowlavg = st.columns(2)
    
    with col_wkts:
        st.markdown("<h4 style='color: #b085f5;'>🎯 Top 10 Career Wickets</h4>", unsafe_allow_html=True)
        wkts_list = leaders.get("wickets", [])
        if wkts_list:
            df_wkts = pd.DataFrame(wkts_list)
            df_wkts.columns = ["Rank", "Player", "Wickets"]
            
            fig = px.bar(
                df_wkts,
                x="Wickets",
                y="Player",
                orientation="h",
                text="Wickets",
                color="Wickets",
                color_continuous_scale="Cividis",
                category_orders={"Player": df_wkts["Player"].tolist()[::-1]}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                showlegend=False,
                coloraxis_showscale=False,
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df_wkts, hide_index=True, use_container_width=True)

    with col_bowlavg:
        st.markdown("<h4 style='color: #00bcd4;'>📉 Top 10 Career Bowling Average (Min. 20 Wickets)</h4>", unsafe_allow_html=True)
        bowl_avg_list = leaders.get("bowling_average", [])
        if bowl_avg_list:
            df_bowl_avg = pd.DataFrame(bowl_avg_list)
            df_bowl_avg.columns = ["Rank", "Player", "Runs Conceded", "Wickets", "Average"]
            
            fig = px.bar(
                df_bowl_avg,
                x="Average",
                y="Player",
                orientation="h",
                text="Average",
                color="Average",
                color_continuous_scale="Tealgrn",
                category_orders={"Player": df_bowl_avg["Player"].tolist()[::-1]}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                showlegend=False,
                coloraxis_showscale=False,
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(
                df_bowl_avg,
                column_config={
                    "Average": st.column_config.NumberColumn(format="%.2f")
                },
                hide_index=True,
                use_container_width=True
            )
