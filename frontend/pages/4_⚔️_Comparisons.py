"""
IPLytics Frontend — Comparisons Page

Side-by-side comparison of players and teams with interactive
charts showing stat differences and head-to-head records.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go

from frontend.api_client import (
    get_players, get_teams,
    compare_players, compare_teams,
)

# --- Page Config ---
st.set_page_config(
    page_title="Comparisons | IPLytics",
    page_icon="⚔️",
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
    .vs-text {
        font-size: 2rem; font-weight: 800;
        color: #f5a623; text-align: center;
        padding: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

COLOR_P1 = "#e94560"
COLOR_P2 = "#0f3460"
COLOR_GOLD = "#f5a623"

with st.sidebar:
    st.markdown("### 🏏 IPLytics")
    st.caption("Comparisons")
    st.divider()


@st.cache_data(ttl=300)
def fetch_players():
    return get_players()


@st.cache_data(ttl=300)
def fetch_teams():
    return get_teams()


# --- Main Content ---
st.title("⚔️ Comparisons")

tab1, tab2 = st.tabs(["🏏 Player vs Player", "🏆 Team vs Team"])

# =============================================
# PLAYER COMPARISON TAB
# =============================================
with tab1:
    st.markdown("### Compare Two Players")

    players = fetch_players()
    if not players:
        st.error("⚠️ Could not load players. Is the backend running?")
    else:
        col1, col_vs, col2 = st.columns([5, 1, 5])

        with col1:
            p1 = st.selectbox(
                "Player 1",
                options=players,
                index=players.index("V Kohli") if "V Kohli" in players else 0,
                key="p1",
            )
        with col_vs:
            st.markdown('<div class="vs-text">VS</div>', unsafe_allow_html=True)
        with col2:
            p2 = st.selectbox(
                "Player 2",
                options=players,
                index=players.index("RG Sharma") if "RG Sharma" in players else 1,
                key="p2",
            )

        if p1 and p2 and p1 != p2:
            data = compare_players(p1, p2)

            if data:
                st.divider()

                # --- Tabs for Batting vs Bowling ---
                comp_tab1, comp_tab2 = st.tabs(["🏏 Batting Stats", "🎳 Bowling Stats"])

                with comp_tab1:
                    b1 = data["player1"]["batting"]
                    b2 = data["player2"]["batting"]

                    # --- Side-by-side Metrics ---
                    st.markdown("#### 📊 Batting Stats")

                    stats_to_show = [
                        ("Matches", "matches", False),
                        ("Runs", "total_runs", True),
                        ("Average", "average", False),
                        ("Strike Rate", "strike_rate", False),
                        ("50s", "fifties", False),
                        ("100s", "hundreds", False),
                    ]

                    for i in range(0, len(stats_to_show), 3):
                        cols = st.columns([5, 1, 5])
                        batch = stats_to_show[i:i+3]

                        with cols[0]:
                            row = st.columns(len(batch))
                            for j, (label, key, fmt_comma) in enumerate(batch):
                                with row[j]:
                                    val = b1[key]
                                    st.metric(label, f"{val:,}" if fmt_comma else f"{val}")

                        with cols[1]:
                            st.write("")  # spacer

                        with cols[2]:
                            row = st.columns(len(batch))
                            for j, (label, key, fmt_comma) in enumerate(batch):
                                with row[j]:
                                    val = b2[key]
                                    st.metric(label, f"{val:,}" if fmt_comma else f"{val}")

                    st.divider()

                    # --- Grouped Bar Chart ---
                    st.markdown("#### 📈 Head-to-Head Comparison")

                    compare_stats = ["total_runs", "average", "strike_rate", "fifties", "hundreds", "sixes"]
                    labels = ["Runs", "Average", "Strike Rate", "50s", "100s", "Sixes"]

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=labels,
                        y=[b1[s] for s in compare_stats],
                        name=b1["name"],
                        marker_color=COLOR_P1,
                        text=[b1[s] for s in compare_stats],
                        textposition="outside",
                        textfont=dict(color="#ccd6f6", size=10),
                    ))
                    fig.add_trace(go.Bar(
                        x=labels,
                        y=[b2[s] for s in compare_stats],
                        name=b2["name"],
                        marker_color=COLOR_P2,
                        text=[b2[s] for s in compare_stats],
                        textposition="outside",
                        textfont=dict(color="#ccd6f6", size=10),
                    ))

                    fig.update_layout(
                        template="plotly_dark",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        barmode="group",
                        height=450, margin=dict(t=30, b=40),
                        font=dict(color="#8892b0"),
                        legend=dict(font=dict(color="#ccd6f6")),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with comp_tab2:
                    bowl1 = data["player1"]["bowling"]
                    bowl2 = data["player2"]["bowling"]

                    if bowl1["matches"] == 0 and bowl2["matches"] == 0:
                        st.info("Neither player has bowling data in the database.")
                    else:
                        # --- Side-by-side Metrics ---
                        st.markdown("#### 📊 Bowling Stats")

                        bowl_stats_show = [
                            ("Matches", "matches", False),
                            ("Overs", "overs_bowled", False),
                            ("Wickets", "wickets", False),
                            ("Runs", "runs_conceded", True),
                            ("Economy", "economy", False),
                            ("Average", "bowling_average", False),
                        ]

                        for i in range(0, len(bowl_stats_show), 3):
                            cols = st.columns([5, 1, 5])
                            batch = bowl_stats_show[i:i+3]

                            with cols[0]:
                                row = st.columns(len(batch))
                                for j, (label, key, fmt_comma) in enumerate(batch):
                                    with row[j]:
                                        val = bowl1[key]
                                        st.metric(label, f"{val:,}" if fmt_comma else f"{val}")

                            with cols[1]:
                                st.write("")  # spacer

                            with cols[2]:
                                row = st.columns(len(batch))
                                for j, (label, key, fmt_comma) in enumerate(batch):
                                    with row[j]:
                                        val = bowl2[key]
                                        st.metric(label, f"{val:,}" if fmt_comma else f"{val}")

                        # Show Best Figures in another row
                        cols = st.columns([5, 1, 5])
                        with cols[0]:
                            row = st.columns(3)
                            with row[0]:
                                st.metric("Best Figures", bowl1["best_figures"])
                        with cols[1]:
                            st.write("")
                        with cols[2]:
                            row = st.columns(3)
                            with row[0]:
                                st.metric("Best Figures", bowl2["best_figures"])

                        st.divider()

                        # --- Grouped Bar Chart ---
                        st.markdown("#### 📈 Bowling Comparison Chart")

                        bowl_compare_stats = ["wickets", "economy", "bowling_average", "bowling_strike_rate"]
                        bowl_labels = ["Wickets", "Economy", "Avg", "SR"]

                        fig_bowl = go.Figure()
                        fig_bowl.add_trace(go.Bar(
                            x=bowl_labels,
                            y=[bowl1[s] for s in bowl_compare_stats],
                            name=bowl1["name"],
                            marker_color=COLOR_P1,
                            text=[bowl1[s] for s in bowl_compare_stats],
                            textposition="outside",
                            textfont=dict(color="#ccd6f6", size=10),
                        ))
                        fig_bowl.add_trace(go.Bar(
                            x=bowl_labels,
                            y=[bowl2[s] for s in bowl_compare_stats],
                            name=bowl2["name"],
                            marker_color=COLOR_P2,
                            text=[bowl2[s] for s in bowl_compare_stats],
                            textposition="outside",
                            textfont=dict(color="#ccd6f6", size=10),
                        ))

                        fig_bowl.update_layout(
                            template="plotly_dark",
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            barmode="group",
                            height=450, margin=dict(t=30, b=40),
                            font=dict(color="#8892b0"),
                            legend=dict(font=dict(color="#ccd6f6")),
                        )
                        st.plotly_chart(fig_bowl, use_container_width=True)

        elif p1 == p2:
            st.info("Please select two different players to compare.")


# =============================================
# TEAM COMPARISON TAB
# =============================================
with tab2:
    st.markdown("### Compare Two Teams")

    teams = fetch_teams()
    if not teams:
        st.error("⚠️ Could not load teams. Is the backend running?")
    else:
        team_names = [t["name"] for t in teams]
        team_display = [f"{t['short_name']} — {t['name']}" for t in teams]

        col1, col_vs, col2 = st.columns([5, 1, 5])

        with col1:
            t1_idx = st.selectbox(
                "Team 1",
                range(len(teams)),
                format_func=lambda i: team_display[i],
                index=team_names.index("Mumbai Indians") if "Mumbai Indians" in team_names else 0,
                key="t1",
            )
        with col_vs:
            st.markdown('<div class="vs-text">VS</div>', unsafe_allow_html=True)
        with col2:
            t2_idx = st.selectbox(
                "Team 2",
                range(len(teams)),
                format_func=lambda i: team_display[i],
                index=team_names.index("Chennai Super Kings") if "Chennai Super Kings" in team_names else 1,
                key="t2",
            )

        t1_name = team_names[t1_idx]
        t2_name = team_names[t2_idx]

        if t1_name != t2_name:
            data = compare_teams(t1_name, t2_name)

            if data:
                s1 = data["team1"]
                s2 = data["team2"]
                h2h = data["head_to_head"]

                st.divider()

                # --- Head-to-Head Highlight ---
                st.markdown("#### ⚔️ Head-to-Head Record")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"{s1['short_name']} Wins", f"{h2h['team1_wins']}")
                with col2:
                    st.metric("Total Matches", f"{h2h['total_matches']}")
                with col3:
                    st.metric(f"{s2['short_name']} Wins", f"{h2h['team2_wins']}")

                # H2H Donut
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    fig = go.Figure(data=[go.Pie(
                        labels=[s1["short_name"], s2["short_name"]],
                        values=[h2h["team1_wins"], h2h["team2_wins"]],
                        hole=0.55,
                        marker_colors=[COLOR_P1, COLOR_P2],
                        textfont=dict(color="#ccd6f6", size=14),
                        textinfo="label+value",
                    )])
                    fig.update_layout(
                        template="plotly_dark",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        height=300, margin=dict(t=10, b=10),
                        font=dict(color="#8892b0"),
                        legend=dict(font=dict(color="#ccd6f6")),
                        annotations=[dict(
                            text=f"{h2h['total_matches']}<br>matches",
                            x=0.5, y=0.5, font_size=16,
                            font_color=COLOR_GOLD,
                            showarrow=False,
                        )],
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.divider()

                # --- Side-by-side Team Stats ---
                st.markdown("#### 📊 Team Stats Comparison")

                team_stats_list = [
                    ("Matches", "total_matches"),
                    ("Wins", "wins"),
                    ("Losses", "losses"),
                    ("Win %", "win_percentage"),
                ]

                col_left, col_mid, col_right = st.columns([5, 1, 5])
                with col_left:
                    st.markdown(f"**{s1['short_name']} — {s1['name']}**")
                    row = st.columns(4)
                    for j, (label, key) in enumerate(team_stats_list):
                        with row[j]:
                            val = s1[key]
                            display = f"{val}%" if key == "win_percentage" else f"{val}"
                            st.metric(label, display)
                with col_mid:
                    st.write("")
                with col_right:
                    st.markdown(f"**{s2['short_name']} — {s2['name']}**")
                    row = st.columns(4)
                    for j, (label, key) in enumerate(team_stats_list):
                        with row[j]:
                            val = s2[key]
                            display = f"{val}%" if key == "win_percentage" else f"{val}"
                            st.metric(label, display)

        elif t1_name == t2_name:
            st.info("Please select two different teams to compare.")
