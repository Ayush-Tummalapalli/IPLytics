"""
IPLytics Frontend — IPL Leaderboards & Stats Page

Displays Orange and Purple Cap histories alongside top 10 career leaderboards
using premium custom HTML tables and stylized Plotly charts.
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

    /* Premium Custom Table Styling */
    .premium-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(233, 69, 96, 0.15);
        background: rgba(26, 26, 46, 0.4);
        color: #ccd6f6;
        font-family: 'Arial', sans-serif;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .premium-table th {
        background-color: rgba(22, 33, 62, 0.8);
        color: #00bcd4;
        font-weight: bold;
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid rgba(233, 69, 96, 0.2);
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.05em;
    }
    .premium-table td {
        padding: 12px 16px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 0.95rem;
    }
    .premium-table tr:last-child td {
        border-bottom: none;
    }
    .premium-table tr:hover {
        background-color: rgba(233, 69, 96, 0.06);
    }
    
    /* Caps Badges */
    .orange-badge {
        background-color: rgba(245, 166, 35, 0.15);
        color: #f5a623;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        border: 1px solid rgba(245, 166, 35, 0.3);
        display: inline-block;
        box-shadow: 0 0 8px rgba(245, 166, 35, 0.1);
    }
    .purple-badge {
        background-color: rgba(176, 133, 245, 0.15);
        color: #b085f5;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        border: 1px solid rgba(176, 133, 245, 0.3);
        display: inline-block;
        box-shadow: 0 0 8px rgba(176, 133, 245, 0.1);
    }

    /* Rank Text Styling */
    .gold-text {
        color: #ffd700;
        font-weight: bold;
    }
    .silver-text {
        color: #c0c0c0;
        font-weight: bold;
    }
    .bronze-text {
        color: #cd7f32;
        font-weight: bold;
    }
    
    /* Header Box */
    .header-box {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.6) 0%, rgba(22, 33, 62, 0.6) 100%);
        border: 1px solid rgba(233, 69, 96, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
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
st.markdown("""
<div class="header-box">
    <h2 style="margin: 0; background: linear-gradient(135deg, #e94560, #f5a623); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800;">🏆 IPL Leaderboards & Caps</h2>
    <p style="margin: 0.5rem 0 0 0; color: #8892b0; font-size: 1.1rem; line-height: 1.4;">Explore dynamic historical cap winners and career top-10 rankings calculated across 18 seasons (2008–2025).</p>
</div>
""", unsafe_allow_html=True)

# Fetch leaderboards from API
with st.spinner("Calculating leaderboard statistics..."):
    data = get_ipl_leaders()

if not data:
    st.error("Could not fetch leaderboards from the database. Please make sure the backend is running.")
    st.stop()

caps = data.get("caps", {})
leaders = data.get("leaderboards", {})

# HTML table helper functions
def clean_html(html_str: str) -> str:
    # Strip carriage returns and newlines, and collapse spaces
    html_str = html_str.replace("\r", "").replace("\n", "")
    while "  " in html_str:
        html_str = html_str.replace("  ", " ")
    return html_str.strip()

def render_caps_table(cap_type, caps_list):
    headers = ["Season", "Player", "Runs Scored" if cap_type == "orange" else "Wickets Taken"]
    badge_class = "orange-badge" if cap_type == "orange" else "purple-badge"
    
    rows_html = ""
    for item in caps_list:
        season = item["season"]
        player = item["player"]
        val = item["value"]
        
        style_attr = "background: rgba(233, 69, 96, 0.04); font-weight: bold;" if season == 2025 else ""
        
        rows_html += f"""
        <tr style="{style_attr}">
            <td style="font-weight: bold; width: 100px;">{season}</td>
            <td>{player}</td>
            <td><span class="{badge_class}">{val:,}</span></td>
        </tr>
        """
        
    table_html = f"""
    <table class="premium-table">
        <thead>
            <tr>
                <th>{headers[0]}</th>
                <th>{headers[1]}</th>
                <th>{headers[2]}</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """
    return clean_html(table_html)

def render_top10_table(headers, data_list, val_key):
    rows_html = ""
    for item in data_list:
        rank = item["rank"]
        player = item["player"]
        val = item[val_key]
        
        rank_str = str(rank)
        if rank == 1:
            rank_str = "🥇 <span class='gold-text'>1</span>"
        elif rank == 2:
            rank_str = "🥈 <span class='silver-text'>2</span>"
        elif rank == 3:
            rank_str = "🥉 <span class='bronze-text'>3</span>"
            
        rows_html += f"""
        <tr>
            <td style="width: 80px; font-weight: bold;">{rank_str}</td>
            <td style="font-weight: 500;">{player}</td>
            <td><strong style="color: #ccd6f6;">{val:,}</strong></td>
        </tr>
        """
        
    table_html = f"""
    <table class="premium-table">
        <thead>
            <tr>
                <th>{headers[0]}</th>
                <th>{headers[1]}</th>
                <th>{headers[2]}</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """
    return clean_html(table_html)

def render_batting_avg_table(data_list):
    rows_html = ""
    for item in data_list:
        rank = item["rank"]
        player = item["player"]
        runs = item["runs"]
        dismissals = item["dismissals"]
        avg = item["value"]
        
        rank_str = str(rank)
        if rank == 1:
            rank_str = "🥇 <span class='gold-text'>1</span>"
        elif rank == 2:
            rank_str = "🥈 <span class='silver-text'>2</span>"
        elif rank == 3:
            rank_str = "🥉 <span class='bronze-text'>3</span>"
            
        rows_html += f"""
        <tr>
            <td style="width: 80px; font-weight: bold;">{rank_str}</td>
            <td style="font-weight: 500;">{player}</td>
            <td>{runs:,}</td>
            <td>{dismissals}</td>
            <td><strong style="color: #00bcd4;">{avg:.2f}</strong></td>
        </tr>
        """
        
    table_html = f"""
    <table class="premium-table">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Total Runs</th>
                <th>Dismissals</th>
                <th>Average</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """
    return clean_html(table_html)

def render_bowling_avg_table(data_list):
    rows_html = ""
    for item in data_list:
        rank = item["rank"]
        player = item["player"]
        runs = item["runs_conceded"]
        wickets = item["wickets"]
        avg = item["value"]
        
        rank_str = str(rank)
        if rank == 1:
            rank_str = "🥇 <span class='gold-text'>1</span>"
        elif rank == 2:
            rank_str = "🥈 <span class='silver-text'>2</span>"
        elif rank == 3:
            rank_str = "🥉 <span class='bronze-text'>3</span>"
            
        rows_html += f"""
        <tr>
            <td style="width: 80px; font-weight: bold;">{rank_str}</td>
            <td style="font-weight: 500;">{player}</td>
            <td>{runs:,}</td>
            <td>{wickets}</td>
            <td><strong style="color: #e94560;">{avg:.2f}</strong></td>
        </tr>
        """
        
    table_html = f"""
    <table class="premium-table">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Runs Conceded</th>
                <th>Wickets</th>
                <th>Average</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """
    return clean_html(table_html)

# Tabs layout
tab_caps, tab_batting, tab_bowling = st.tabs([
    "🥇 Season Caps",
    "🏏 Batting Leaders",
    "🥎 Bowling Leaders"
])

with tab_caps:
    st.markdown("<h3 style='margin-top: 1rem; color: #ccd6f6;'>Historical Orange & Purple Cap Winners</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8892b0; margin-bottom: 2rem;'>Below is the season-wise list of top-performing batters and bowlers from every IPL edition.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h4 style='color: #f5a623; margin-bottom: 1rem;'>🟠 Orange Cap Winners (Most Runs)</h4>", unsafe_allow_html=True)
        orange_list = caps.get("orange", [])
        if orange_list:
            st.markdown(render_caps_table("orange", orange_list), unsafe_allow_html=True)
        else:
            st.info("No Orange Cap data available.")

    with col2:
        st.markdown("<h4 style='color: #b085f5; margin-bottom: 1rem;'>🟣 Purple Cap Winners (Most Wickets)</h4>", unsafe_allow_html=True)
        purple_list = caps.get("purple", [])
        if purple_list:
            st.markdown(render_caps_table("purple", purple_list), unsafe_allow_html=True)
        else:
            st.info("No Purple Cap data available.")

with tab_batting:
    st.markdown("<h3 style='margin-top: 1rem; color: #ccd6f6;'>All-Time Batting Leaderboards</h3>", unsafe_allow_html=True)
    
    col_runs, col_sixes = st.columns(2)
    
    with col_runs:
        st.markdown("<h4 style='color: #00bcd4; margin-bottom: 1rem;'>📈 Top 10 Career Runs</h4>", unsafe_allow_html=True)
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
                color_discrete_sequence=["#00bcd4"],
                category_orders={"Player": df_runs["Player"].tolist()[::-1]}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Total Runs"),
                yaxis=dict(showgrid=False, title=""),
                showlegend=False,
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            fig.update_traces(textposition="inside", hovertemplate="<b>%{y}</b><br>Runs: %{x:,}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(render_top10_table(["Rank", "Player", "Total Runs"], runs_list, "value"), unsafe_allow_html=True)

    with col_sixes:
        st.markdown("<h4 style='color: #e94560; margin-bottom: 1rem;'>💥 Top 10 Career Sixes</h4>", unsafe_allow_html=True)
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
                color_discrete_sequence=["#e94560"],
                category_orders={"Player": df_sixes["Player"].tolist()[::-1]}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Total Sixes"),
                yaxis=dict(showgrid=False, title=""),
                showlegend=False,
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            fig.update_traces(textposition="inside", hovertemplate="<b>%{y}</b><br>Sixes: %{x:,}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(render_top10_table(["Rank", "Player", "Total Sixes"], sixes_list, "value"), unsafe_allow_html=True)
            
    st.divider()
    
    st.markdown("<h4 style='color: #00bcd4; margin-bottom: 1rem; margin-top: 1rem;'>🔥 Top 10 Batting Average (Min. 20 Innings)</h4>", unsafe_allow_html=True)
    avg_list = leaders.get("batting_average", [])
    if avg_list:
        st.markdown(render_batting_avg_table(avg_list), unsafe_allow_html=True)

with tab_bowling:
    st.markdown("<h3 style='margin-top: 1rem; color: #ccd6f6;'>All-Time Bowling Leaderboards</h3>", unsafe_allow_html=True)
    
    col_wkts, col_bowlavg = st.columns(2)
    
    with col_wkts:
        st.markdown("<h4 style='color: #b085f5; margin-bottom: 1rem;'>🎯 Top 10 Career Wickets</h4>", unsafe_allow_html=True)
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
                color_discrete_sequence=["#b085f5"],
                category_orders={"Player": df_wkts["Player"].tolist()[::-1]}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Total Wickets"),
                yaxis=dict(showgrid=False, title=""),
                showlegend=False,
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            fig.update_traces(textposition="inside", hovertemplate="<b>%{y}</b><br>Wickets: %{x:,}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(render_top10_table(["Rank", "Player", "Total Wickets"], wkts_list, "value"), unsafe_allow_html=True)

    with col_bowlavg:
        st.markdown("<h4 style='color: #e94560; margin-bottom: 1rem;'>📉 Top 10 Career Bowling Average (Min. 20 Wickets)</h4>", unsafe_allow_html=True)
        bowl_avg_list = leaders.get("bowling_average", [])
        if bowl_avg_list:
            df_bowl_avg = pd.DataFrame(bowl_avg_list)
            df_bowl_avg = df_bowl_avg[["rank", "player", "value"]]
            df_bowl_avg.columns = ["Rank", "Player", "Average"]
            
            fig = px.bar(
                df_bowl_avg,
                x="Average",
                y="Player",
                orientation="h",
                text="Average",
                color_discrete_sequence=["#e94560"],
                category_orders={"Player": df_bowl_avg["Player"].tolist()[::-1]}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Bowling Average (Lower is Better)"),
                yaxis=dict(showgrid=False, title=""),
                showlegend=False,
                height=300,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            fig.update_traces(textposition="inside", hovertemplate="<b>%{y}</b><br>Average: %{x:.2f}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(render_bowling_avg_table(bowl_avg_list), unsafe_allow_html=True)
