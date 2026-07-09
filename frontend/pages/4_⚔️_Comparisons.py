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

import pandas as pd
import plotly.express as px

from frontend.api_client import (
    get_players, get_teams,
    compare_players, compare_teams,
    get_matchup_stats,
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
     .vs-text {
        font-size: 2rem; font-weight: 800;
        color: #f5a623; text-align: center;
        padding: 2rem 0;
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
    
    /* Badges */
    .orange-badge {
        background-color: rgba(245, 166, 35, 0.15);
        color: #f5a623;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        border: 1px solid rgba(245, 166, 35, 0.3);
        display: inline-block;
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
    }

    /* Premium Team Comparisons Cards styling */
    .team-card {
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .team-card:hover {
        transform: translateY(-4px);
    }
    .team-card-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
        font-weight: 500;
    }
    .team-card-value {
        font-size: 1.8rem;
        font-weight: 800;
    }
    
    .team-default {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #e9456030;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.1);
    }
    .team-default:hover {
        border-color: #e9456080;
        box-shadow: 0 12px 30px rgba(233, 69, 96, 0.25);
    }
    .team-default .team-card-label { color: #8892b0; }
    .team-default .team-card-value { color: #e94560; }
    
    /* CSK */
    .team-CSK {
        background: linear-gradient(135deg, #FFF9C4 0%, #FBC02D 100%);
        border: 1px solid #FFD70080;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2);
    }
    .team-CSK:hover {
        border-color: #FFD700;
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
    }
    .team-CSK .team-card-label { color: #002F6C80; }
    .team-CSK .team-card-value { color: #002F6C; }
    
    /* MI */
    .team-MI {
        background: linear-gradient(135deg, #1A237E 0%, #0D47A1 100%);
        border: 1px solid #00D4FF80;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
    }
    .team-MI:hover {
        border-color: #00D4FF;
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
    }
    .team-MI .team-card-label { color: #8892b0; }
    .team-MI .team-card-value { color: #FFFFFF; }
    
    /* RCB */
    .team-RCB {
        background: linear-gradient(135deg, #1A1A1A 0%, #2D0000 100%);
        border: 1px solid #E9456080;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.2);
    }
    .team-RCB:hover {
        border-color: #E94560;
        box-shadow: 0 8px 25px rgba(233, 69, 96, 0.4);
    }
    .team-RCB .team-card-label { color: #8892b0; }
    .team-RCB .team-card-value { color: #FFFFFF; }

    /* KKR */
    .team-KKR {
        background: linear-gradient(135deg, #311B92 0%, #1A237E 100%);
        border: 1px solid #FFD70080;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2);
    }
    .team-KKR:hover {
        border-color: #FFD700;
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
    }
    .team-KKR .team-card-label { color: #8892b0; }
    .team-KKR .team-card-value { color: #FFFFFF; }

    /* SRH */
    .team-SRH {
        background: linear-gradient(135deg, #FF6F00 0%, #E65100 100%);
        border: 1px solid #00000080;
        box-shadow: 0 4px 15px rgba(255, 111, 0, 0.2);
    }
    .team-SRH:hover {
        border-color: #000000;
        box-shadow: 0 8px 25px rgba(255, 111, 0, 0.4);
    }
    .team-SRH .team-card-label { color: #8892b0; }
    .team-SRH .team-card-value { color: #FFFFFF; }

    /* DC */
    .team-DC {
        background: linear-gradient(135deg, #0D47A1 0%, #D50000 100%);
        border: 1px solid #FFFFFF80;
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
    }
    .team-DC:hover {
        border-color: #FFFFFF;
        box-shadow: 0 8px 25px rgba(255, 255, 255, 0.3);
    }
    .team-DC .team-card-label { color: #8892b0; }
    .team-DC .team-card-value { color: #FFFFFF; }

    /* RR */
    .team-RR {
        background: linear-gradient(135deg, #C2185B 0%, #0D47A1 100%);
        border: 1px solid #00D4FF80;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
    }
    .team-RR:hover {
        border-color: #00D4FF;
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
    }
    .team-RR .team-card-label { color: #8892b0; }
    .team-RR .team-card-value { color: #FFFFFF; }

    /* PBKS */
    .team-PBKS {
        background: linear-gradient(135deg, #D50000 0%, #B71C1C 100%);
        border: 1px solid #FFD70080;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2);
    }
    .team-PBKS:hover {
        border-color: #FFD700;
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
    }
    .team-PBKS .team-card-label { color: #8892b0; }
    .team-PBKS .team-card-value { color: #FFFFFF; }

    /* GT */
    .team-GT {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border: 1px solid #D4AF3780;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.1);
    }
    .team-GT:hover {
        border-color: #D4AF37;
        box-shadow: 0 8px 25px rgba(212, 175, 55, 0.3);
    }
    .team-GT .team-card-label { color: #8892b0; }
    .team-GT .team-card-value { color: #FFFFFF; }

    /* LSG */
    .team-LSG {
        background: linear-gradient(135deg, #E0F7FA 0%, #80DEEA 100%);
        border: 1px solid #FFB30080;
        box-shadow: 0 4px 15px rgba(255, 179, 0, 0.2);
    }
    .team-LSG:hover {
        border-color: #FFB300;
        box-shadow: 0 8px 25px rgba(255, 179, 0, 0.4);
    }
    .team-LSG .team-card-label { color: #0D47A180; }
    .team-LSG .team-card-value { color: #0D47A1; }
</style>
""", unsafe_allow_html=True)

def render_team_metric_card(label: str, value: str, short_name: str) -> str:
    clean_short = short_name.upper().replace(" ", "")
    class_name = f"team-{clean_short}"
    supported = ["CSK", "MI", "RCB", "KKR", "SRH", "DC", "RR", "PBKS", "GT", "LSG"]
    if clean_short not in supported:
        class_name = "team-default"
    return f"""
    <div class="team-card {class_name}">
        <div class="team-card-label">{label}</div>
        <div class="team-card-value">{value}</div>
    </div>
    """

def clean_html(html_str: str) -> str:
    html_str = html_str.replace("\r", "").replace("\n", "")
    while "  " in html_str:
        html_str = html_str.replace("  ", " ")
    return html_str.strip()

COLOR_P1 = "#e94560"
COLOR_P2 = "#0f3460"
COLOR_GOLD = "#f5a623"

def render_batting_radar(b1, b2):
    # Calculate values
    avg1 = b1.get("average", 0) or 0
    sr1 = b1.get("strike_rate", 0) or 0
    fours1 = b1.get("fours", 0) or 0
    sixes1 = b1.get("sixes", 0) or 0
    balls1 = b1.get("balls_faced", 1) or 1
    matches1 = b1.get("matches", 1) or 1
    runs1 = b1.get("total_runs", 0) or 0
    not_outs1 = b1.get("not_outs", 0) or 0
    
    bd_pct1 = (fours1 + sixes1) / balls1 * 100
    rpm1 = runs1 / matches1
    no_pct1 = not_outs1 / matches1 * 100
    
    avg2 = b2.get("average", 0) or 0
    sr2 = b2.get("strike_rate", 0) or 0
    fours2 = b2.get("fours", 0) or 0
    sixes2 = b2.get("sixes", 0) or 0
    balls2 = b2.get("balls_faced", 1) or 1
    matches2 = b2.get("matches", 1) or 1
    runs2 = b2.get("total_runs", 0) or 0
    not_outs2 = b2.get("not_outs", 0) or 0
    
    bd_pct2 = (fours2 + sixes2) / balls2 * 100
    rpm2 = runs2 / matches2
    no_pct2 = not_outs2 / matches2 * 100

    # Scale to 0-100 relative to benchmarks
    s_avg1 = min(100.0, (avg1 / 50.0) * 100.0)
    s_sr1 = min(100.0, (sr1 / 160.0) * 100.0)
    s_bd1 = min(100.0, (bd_pct1 / 25.0) * 100.0)
    s_rpm1 = min(100.0, (rpm1 / 45.0) * 100.0)
    s_no1 = min(100.0, (no_pct1 / 40.0) * 100.0)
    
    s_avg2 = min(100.0, (avg2 / 50.0) * 100.0)
    s_sr2 = min(100.0, (sr2 / 160.0) * 100.0)
    s_bd2 = min(100.0, (bd_pct2 / 25.0) * 100.0)
    s_rpm2 = min(100.0, (rpm2 / 45.0) * 100.0)
    s_no2 = min(100.0, (no_pct2 / 40.0) * 100.0)
    
    categories = ['Average', 'Strike Rate', 'Boundary %', 'Runs/Match', 'Not Out %']
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[s_avg1, s_sr1, s_bd1, s_rpm1, s_no1, s_avg1],
        theta=categories + [categories[0]],
        fill='toself',
        name=b1["name"],
        line_color=COLOR_P1,
        text=[f"Avg: {avg1}", f"SR: {sr1}", f"Boundaries: {bd_pct1:.1f}%", f"Runs/Match: {rpm1:.1f}", f"Not Out: {no_pct1:.1f}%", f"Avg: {avg1}"],
        hovertemplate="%{text}"
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[s_avg2, s_sr2, s_bd2, s_rpm2, s_no2, s_avg2],
        theta=categories + [categories[0]],
        fill='toself',
        name=b2["name"],
        line_color="#00bcd4" if COLOR_P2 == "#0f3460" else COLOR_P2,  # use cyan for better contrast if COLOR_P2 is dark
        text=[f"Avg: {avg2}", f"SR: {sr2}", f"Boundaries: {bd_pct2:.1f}%", f"Runs/Match: {rpm2:.1f}", f"Not Out: {no_pct2:.1f}%", f"Avg: {avg2}"],
        hovertemplate="%{text}"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False
            )
        ),
        showlegend=True,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=40, l=40, r=40),
        height=400,
    )
    return fig

def render_bowling_radar(bowl1, bowl2):
    # P1
    w1 = bowl1.get("wickets", 0) or 0
    m1 = bowl1.get("matches", 1) or 1
    econ1 = bowl1.get("economy", 8.0) or 8.0
    avg1 = bowl1.get("bowling_average", 30.0) or 30.0
    sr1 = bowl1.get("bowling_strike_rate", 20.0) or 20.0
    overs1 = bowl1.get("overs_bowled", 0.0) or 0.0
    
    wpm1 = w1 / m1
    opm1 = overs1 / m1
    
    # P2
    w2 = bowl2.get("wickets", 0) or 0
    m2 = bowl2.get("matches", 1) or 1
    econ2 = bowl2.get("economy", 8.0) or 8.0
    avg2 = bowl2.get("bowling_average", 30.0) or 30.0
    sr2 = bowl2.get("bowling_strike_rate", 20.0) or 20.0
    overs2 = bowl2.get("overs_bowled", 0.0) or 0.0
    
    wpm2 = w2 / m2
    opm2 = overs2 / m2

    # Scale to 0-100 relative to benchmarks
    s_wpm1 = min(100.0, (wpm1 / 1.5) * 100.0)
    s_econ1 = min(100.0, max(0.0, (12.0 - econ1) / (12.0 - 6.5) * 100.0))
    s_avg1 = min(100.0, max(0.0, (40.0 - avg1) / (40.0 - 20.0) * 100.0))
    s_sr1 = min(100.0, max(0.0, (30.0 - sr1) / (30.0 - 15.0) * 100.0))
    s_opm1 = min(100.0, (opm1 / 4.0) * 100.0)
    
    s_wpm2 = min(100.0, (wpm2 / 1.5) * 100.0)
    s_econ2 = min(100.0, max(0.0, (12.0 - econ2) / (12.0 - 6.5) * 100.0))
    s_avg2 = min(100.0, max(0.0, (40.0 - avg2) / (40.0 - 20.0) * 100.0))
    s_sr2 = min(100.0, max(0.0, (30.0 - sr2) / (30.0 - 15.0) * 100.0))
    s_opm2 = min(100.0, (opm2 / 4.0) * 100.0)
    
    categories = ['Wickets/Match', 'Economy', 'Average', 'Strike Rate', 'Overs/Match']
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[s_wpm1, s_econ1, s_avg1, s_sr1, s_opm1, s_wpm1],
        theta=categories + [categories[0]],
        fill='toself',
        name=bowl1["name"],
        line_color=COLOR_P1,
        text=[f"Wickets/Match: {wpm1:.2f}", f"Economy: {econ1}", f"Avg: {avg1}", f"SR: {sr1}", f"Overs/Match: {opm1:.1f}", f"Wickets/Match: {wpm1:.2f}"],
        hovertemplate="%{text}"
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[s_wpm2, s_econ2, s_avg2, s_sr2, s_opm2, s_wpm2],
        theta=categories + [categories[0]],
        fill='toself',
        name=bowl2["name"],
        line_color="#00bcd4" if COLOR_P2 == "#0f3460" else COLOR_P2,  # use cyan for better contrast if COLOR_P2 is dark
        text=[f"Wickets/Match: {wpm2:.2f}", f"Economy: {econ2}", f"Avg: {avg2}", f"SR: {sr2}", f"Overs/Match: {opm2:.1f}", f"Wickets/Match: {wpm2:.2f}"],
        hovertemplate="%{text}"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False
            )
        ),
        showlegend=True,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=40, l=40, r=40),
        height=400,
    )
    return fig

with st.sidebar:
    st.markdown("### 🏏 IPLytics")
    st.caption("Comparisons")
    st.divider()
    
    st.markdown("#### ⚔️ Comparison Guide")
    st.markdown(clean_html("""
    <div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(233, 69, 96, 0.15); border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        <h6 style="margin: 0 0 0.4rem 0; color: #e94560; font-weight: 700;">🧑 Player Comparison</h6>
        <p style="font-size: 0.82rem; color: #8892b0; margin-bottom: 0.8rem; line-height: 1.3;">Compare batting averages, strike rates, wickets, and economy metrics side-by-side.</p>
        
        <h6 style="margin: 0 0 0.4rem 0; color: #00bcd4; font-weight: 700;">🏆 Team Comparison</h6>
        <p style="font-size: 0.82rem; color: #8892b0; margin-bottom: 0.8rem; line-height: 1.3;">Analyze head-to-head ratios, season performance trends, and win/loss methods.</p>
        
        <h6 style="margin: 0 0 0.4rem 0; color: #f5a623; font-weight: 700;">⚔️ Batter vs Bowler</h6>
        <p style="font-size: 0.82rem; color: #8892b0; margin-bottom: 0; line-height: 1.3;">Deep-dive into carrier matchups: runs, wickets, strike rate, boundaries, and dot balls.</p>
    </div>
    """), unsafe_allow_html=True)


@st.cache_data(ttl=300)
def fetch_players():
    return get_players()


@st.cache_data(ttl=300)
def fetch_teams():
    return get_teams()


# --- Main Content ---
st.title("⚔️ Comparisons")

tab1, tab2, tab3 = st.tabs(["🏏 Player vs Player", "🏆 Team vs Team", "⚔️ Batter vs Bowler Matchup"])

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
                    
                    # --- Batting Radar Chart ---
                    st.markdown("#### 🕸️ Player Performance Radar")
                    fig = render_batting_radar(b1, b2)
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

                        # --- Bowling Radar Chart ---
                        st.markdown("#### 🕸️ Player Bowling Radar")
                        fig_bowl = render_bowling_radar(bowl1, bowl2)
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
                            st.markdown(clean_html(render_team_metric_card(label, display, s1['short_name'])), unsafe_allow_html=True)
                with col_mid:
                    st.write("")
                with col_right:
                    st.markdown(f"**{s2['short_name']} — {s2['name']}**")
                    row = st.columns(4)
                    for j, (label, key) in enumerate(team_stats_list):
                        with row[j]:
                            val = s2[key]
                            display = f"{val}%" if key == "win_percentage" else f"{val}"
                            st.markdown(clean_html(render_team_metric_card(label, display, s2['short_name'])), unsafe_allow_html=True)

        elif t1_name == t2_name:
            st.info("Please select two different teams to compare.")


# =============================================
# BATTER VS BOWLER MATCHUP TAB
# =============================================
with tab3:
    st.markdown("### Batter vs Bowler Head-to-Head (H2H) Matchup")
    st.markdown("<p style='color: #8892b0; margin-bottom: 2rem;'>Select any batter and bowler to inspect their career rivalry statistics computed from ball-by-ball records.</p>", unsafe_allow_html=True)

    players = fetch_players()
    if not players:
        st.error("⚠️ Could not load players. Is the backend running?")
    else:
        col_bat, col_vs_m, col_bowl = st.columns([5, 1, 5])

        with col_bat:
            selected_batter = st.selectbox(
                "Select Batter",
                options=players,
                index=players.index("V Kohli") if "V Kohli" in players else 0,
                key="matchup_batter",
            )
        with col_vs_m:
            st.markdown('<div class="vs-text">VS</div>', unsafe_allow_html=True)
        with col_bowl:
            selected_bowler = st.selectbox(
                "Select Bowler",
                options=players,
                index=players.index("JJ Bumrah") if "JJ Bumrah" in players else 1,
                key="matchup_bowler",
            )

        if selected_batter and selected_bowler:
            with st.spinner(f"Fetching matchup stats between {selected_batter} and {selected_bowler}..."):
                matchup_data = get_matchup_stats(selected_batter, selected_bowler)

            if matchup_data and matchup_data.get("overall"):
                overall = matchup_data["overall"]
                seasons = matchup_data["seasons"]

                # Check if they have ever faced each other
                total_balls = overall.get("balls", 0)
                if total_balls == 0:
                    st.warning(f"⚠️ {selected_batter} has never faced {selected_bowler} in any IPL match.")
                else:
                    # Show key metrics in metric cards
                    st.markdown("#### ⚡ Overall Matchup Aggregates")
                    
                    cols = st.columns(7)
                    metrics = [
                        ("Runs", f"{overall['runs']}", None),
                        ("Balls Faced", f"{overall['balls']}", None),
                        ("Strike Rate", f"{overall['strike_rate']:.2f}", None),
                        ("Dismissals", f"{overall['dismissals']}", None),
                        ("Fours", f"{overall['fours']}", None),
                        ("Sixes", f"{overall['sixes']}", None),
                        ("Dot Balls", f"{overall['dots']}", None),
                    ]
                    for col, (label, val, delta) in zip(cols, metrics):
                        col.metric(label=label, value=val, delta=delta)

                    st.write("")
                    st.divider()

                    # Charts & Tables Side-by-Side
                    col_chart, col_table = st.columns([6, 5])

                    with col_chart:
                        st.markdown("#### 📈 Season-by-Season Performance")
                        if seasons:
                            df_seasons = pd.DataFrame(seasons)
                            df_seasons["season"] = df_seasons["season"].astype(str)

                            fig = go.Figure()
                            
                            # Add Runs as Line
                            fig.add_trace(go.Scatter(
                                x=df_seasons["season"],
                                y=df_seasons["runs"],
                                name="Runs Scored",
                                mode="lines+markers",
                                line=dict(color="#e94560", width=3),
                                marker=dict(size=8),
                                hovertemplate="<b>%{x}</b><br>Runs: %{y}<extra></extra>"
                            ))

                            # Add Wickets as Bar
                            fig.add_trace(go.Bar(
                                x=df_seasons["season"],
                                y=df_seasons["dismissals"],
                                name="Dismissals",
                                marker_color="#b085f5",
                                opacity=0.8,
                                hovertemplate="<b>%{x}</b><br>Dismissals: %{y}<extra></extra>"
                            ))

                            fig.update_layout(
                                template="plotly_dark",
                                plot_bgcolor="rgba(0,0,0,0)",
                                paper_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="#8892b0"),
                                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Season"),
                                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Count"),
                                legend=dict(x=0.01, y=0.99, bgcolor="rgba(26, 26, 46, 0.6)"),
                                height=350,
                                margin=dict(t=20, b=20, l=20, r=20),
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No season breakdown available.")

                    with col_table:
                        st.markdown("#### 📋 Season-by-Season Breakdown")
                        if seasons:
                            def clean_table_html(html_str: str) -> str:
                                html_str = html_str.replace("\r", "").replace("\n", "")
                                while "  " in html_str:
                                    html_str = html_str.replace("  ", " ")
                                return html_str.strip()

                            rows_html = ""
                            for s in seasons:
                                row_style = "background: rgba(233, 69, 96, 0.04); font-weight: bold;" if s['dismissals'] > 0 else ""
                                rows_html += f"""
                                <tr style="{row_style}">
                                    <td style="font-weight: bold; width: 100px;">{s['season']}</td>
                                    <td><strong>{s['runs']}</strong></td>
                                    <td>{s['balls']}</td>
                                    <td><strong style='color: #00bcd4;'>{s['strike_rate']:.2f}</strong></td>
                                    <td>
                                        <span class="{'purple-badge' if s['dismissals'] > 0 else ''}">
                                            {s['dismissals']}
                                        </span>
                                    </td>
                                </tr>
                                """

                            table_html = f"""
                            <table class="premium-table">
                                <thead>
                                    <tr>
                                        <th>Season</th>
                                        <th>Runs</th>
                                        <th>Balls</th>
                                        <th>Strike Rate</th>
                                        <th>Dismissals</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows_html}
                                </tbody>
                            </table>
                            """
                            st.markdown(clean_table_html(table_html), unsafe_allow_html=True)
                        else:
                            st.info("No season breakdown data available.")
            else:
                st.error("⚠️ Failed to load matchup details from the server.")
