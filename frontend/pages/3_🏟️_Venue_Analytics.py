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

def clean_html(html_str: str) -> str:
    """Strip leading/trailing whitespace from each line to prevent Streamlit rendering issues."""
    return "\n".join([line.strip() for line in html_str.strip().splitlines()])

# --- Page Config ---
st.set_page_config(
    page_title="Venue Analytics | IPLytics",
    page_icon="🏟️",
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

    # ── Sidebar dynamic profile card ──
    with st.sidebar:
        venue_franchises = {
            "Wankhede Stadium": "⚡ Mumbai Indians",
            "MA Chidambaram Stadium": "🦁 Chennai Super Kings",
            "M Chinnaswamy Stadium": "🦅 Royal Challengers Bengaluru",
            "M.Chinnaswamy Stadium": "🦅 Royal Challengers Bengaluru",
            "Eden Gardens": "🛡️ Kolkata Knight Riders",
            "Rajiv Gandhi International Stadium": "🦅 Sunrisers Hyderabad",
            "Arun Jaitley Stadium": "🐯 Delhi Capitals",
            "Feroz Shah Kotla": "🐯 Delhi Capitals",
            "Sawai Mansingh Stadium": "👑 Rajasthan Royals",
            "Punjab Cricket Association": "🦁 Punjab Kings",
            "Narendra Modi Stadium": "⚡ Gujarat Titans",
            "Ekana Cricket Stadium": "🦅 Lucknow Super Giants",
            "Ekana Cricket": "🦅 Lucknow Super Giants",
            "Deccan": "🛡️ Deccan Chargers"
        }
        
        home_team = "Neutral / Multi-Team"
        for k, v in venue_franchises.items():
            if k.lower() in stats['venue'].lower():
                home_team = v
                break
                
        st.markdown("#### 🏟️ Venue Profile Summary")
        st.markdown(f"""
        <div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(233, 69, 96, 0.15); border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h5 style="margin: 0 0 0.5rem 0; color: #f5a623; font-size: 1.1rem; font-weight: 700;">{stats['venue']}</h5>
            <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">📍 City: <strong>{stats['city']}</strong></div>
            <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">🏠 Home Team: <strong>{home_team}</strong></div>
            <div style="font-size: 0.9rem; color: #ccd6f6; margin-bottom: 0.4rem;">🏏 Avg 1st Inn Score: <strong>{stats['avg_first_innings_score']}</strong></div>
            <div style="font-size: 0.9rem; color: #ccd6f6;">🏏 Avg 2nd Inn Score: <strong>{stats['avg_second_innings_score']}</strong></div>
        </div>
        """, unsafe_allow_html=True)

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
    # TACTICAL PITCH & BOUNDARY GUIDE
    # =============================================
    st.markdown("#### 🏟️ Pitch & Boundary Tactical Guide")
    
    stadium_details = {
        "wankhede": {
            "soil": "🔴 Red Soil (High bounce, extra pace)",
            "off": 64, "leg": 68, "str": 72,
            "pace": 68, "spin": 32,
            "desc": "Wankhede features a quick outfield and true bounce, making it highly batting-friendly. Pace bowlers get swing early on, but spin becomes hard to control due to short boundaries."
        },
        "chidambaram": {
            "soil": "⚫ Black Soil (Slow, turns, low bounce)",
            "off": 66, "leg": 66, "str": 70,
            "pace": 45, "spin": 55,
            "desc": "Chepauk is famous for dry, abrasive pitches that assist spinners and slower bowlers. Batting first is generally preferred as the pitch slows down significantly in the second innings."
        },
        "chinnaswamy": {
            "soil": "🔴 Red Soil (Fast, high bounce, flat deck)",
            "off": 60, "leg": 62, "str": 65,
            "pace": 65, "spin": 35,
            "desc": "A batsman's paradise with very short boundaries. High altitude and flat pitches mean huge totals are common and no target is safe. Spinners must bowl defensive lines."
        },
        "eden gardens": {
            "soil": "🔴⚫ Mixed Soil (Balanced bounce & turn)",
            "off": 66, "leg": 68, "str": 72,
            "pace": 60, "spin": 40,
            "desc": "Historically spin-friendly, but has transitioned into a fast, bouncing track with a lightning-fast outfield. Both pacers and spinners get assistance depending on the time of day."
        },
        "rajiv gandhi": {
            "soil": "⚫ Black Soil (Dry, aids turn and seam)",
            "off": 68, "leg": 70, "str": 75,
            "pace": 58, "spin": 42,
            "desc": "Uppal has relatively large boundaries that encourage bowlers to use flight and variations. A balanced pitch that provides equal opportunity to both batsmen and disciplined bowlers."
        },
        "arun jaitley": {
            "soil": "⚫ Black Soil (Low bounce, aids spin & slow cutters)",
            "off": 63, "leg": 65, "str": 68,
            "pace": 52, "spin": 48,
            "desc": "Kotla has short boundaries but a slow, low pitch. Batsmen can score heavily if they get in, but spinners dominate the middle overs as the ball stops and grips."
        },
        "sawai mansingh": {
            "soil": "⚫ Black Soil (Heavy clay, balanced bounce)",
            "off": 70, "leg": 72, "str": 78,
            "pace": 50, "spin": 50,
            "desc": "Featuring massive square and straight boundaries, boundary-hitting is difficult here. Running between wickets is crucial, and spin bowlers are highly effective using the big outfield."
        },
        "narendra modi": {
            "soil": "🔴⚫ Multi-Soil Pitches (Varied bounce, lightning outfield)",
            "off": 72, "leg": 74, "str": 80,
            "pace": 70, "spin": 30,
            "desc": "The world's largest stadium features extra bounce and speed. Wide square boundaries make six-hitting a challenge, rewarding bowlers who extract seam movement and bowl hard lengths."
        },
        "ekana": {
            "soil": "⚫ Black Soil (Extremely dry, slow, dust-bowl potential)",
            "off": 68, "leg": 72, "str": 78,
            "pace": 40, "spin": 60,
            "desc": "A slow-turn pitch where spinners are lethal. Wickets fall to flight and grip. Scoring runs is hard work, making 140-150 highly competitive scores."
        }
    }

    venue_key = "generic"
    venue_lower = stats['venue'].lower()
    for k in stadium_details.keys():
        if k in venue_lower:
            venue_key = k
            break
            
    details = stadium_details.get(venue_key, {
        "soil": "🔴⚫ Clay Soil (Standard balanced pitch)",
        "off": 67, "leg": 68, "str": 73,
        "pace": 58, "spin": 42,
        "desc": "A standard balanced IPL pitch offering equal contest between bat and ball. Pace bowlers find movement early under lights, while spinners get grip during the middle overs."
    })

    col_pitch, col_boundary = st.columns([1, 1])

    with col_pitch:
        st.markdown(clean_html(f"""
        <div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(233, 69, 96, 0.15); border-radius: 12px; padding: 1.25rem; height: 350px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <h5 style="margin: 0 0 0.75rem 0; color: #e94560; font-weight: 700; font-size: 1.15rem;">📊 Pitch Conditions</h5>
                <div style="margin-bottom: 0.75rem; font-size: 0.95rem; color: #ccd6f6;">🧱 Soil Type: <strong>{details['soil']}</strong></div>
                <p style="font-size: 0.88rem; color: #8892b0; line-height: 1.55; margin: 0;">{details['desc']}</p>
            </div>
            <div style="margin-top: 1rem; border-top: 1px solid rgba(233, 69, 96, 0.1); padding-top: 0.75rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.25rem; color: #ccd6f6;">
                    <span>🔥 Pace Wickets split:</span>
                    <strong>{details['pace']}%</strong>
                </div>
                <div style="background: rgba(255,255,255,0.05); height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 0.75rem;">
                    <div style="background: #e94560; width: {details['pace']}%; height: 100%;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.25rem; color: #ccd6f6;">
                    <span>🌀 Spin Wickets split:</span>
                    <strong>{details['spin']}%</strong>
                </div>
                <div style="background: rgba(255,255,255,0.05); height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #f5a623; width: {details['spin']}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)

    with col_boundary:
        st.markdown(clean_html(f"""
        <div style="background: rgba(26, 26, 46, 0.4); border: 1px solid rgba(233, 69, 96, 0.15); border-radius: 12px; padding: 1.25rem; height: 350px; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;">
            <h5 style="margin: 0; color: #f5a623; position: absolute; top: 1.25rem; left: 1.25rem; font-weight: 700; font-size: 1.15rem;">📐 Boundary Lengths</h5>
            <div style="width: 100%; display: flex; justify-content: center; margin-top: 2rem;">
                <svg viewBox="0 0 340 240" width="100%" height="240" style="max-width: 340px;">
                    <defs>
                        <radialGradient id="fieldGrad" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stop-color="#143e21" />
                            <stop offset="100%" stop-color="#0a2212" />
                        </radialGradient>
                    </defs>
                    <!-- Cricket Turf Field -->
                    <ellipse cx="170" cy="125" rx="100" ry="80" fill="url(#fieldGrad)" stroke="#1c502b" stroke-width="2.5" />
                    
                    <!-- 30-Yard Circle -->
                    <ellipse cx="170" cy="125" rx="55" ry="44" fill="none" stroke="rgba(255, 255, 255, 0.18)" stroke-width="1.2" stroke-dasharray="3" />
                    
                    <!-- Center Pitch -->
                    <rect x="166" y="110" width="8" height="30" fill="#dfc08a" rx="1" />
                    <line x1="164" y1="113" x2="176" y2="113" stroke="white" stroke-width="0.8" opacity="0.5"/>
                    <line x1="164" y1="137" x2="176" y2="137" stroke="white" stroke-width="0.8" opacity="0.5"/>
                    
                    <!-- Rope Boundary line -->
                    <ellipse cx="170" cy="125" rx="90" ry="72" fill="none" stroke="#e94560" stroke-width="3" opacity="0.9" />
                    
                    <!-- Measurements -->
                    <!-- Straight -->
                    <line x1="170" y1="110" x2="170" y2="53" stroke="#f5a623" stroke-width="1.5" stroke-dasharray="3"/>
                    <circle cx="170" cy="53" r="3" fill="#f5a623" />
                    <rect x="125" y="12" width="90" height="20" rx="4" fill="rgba(15, 15, 35, 0.9)" stroke="rgba(245, 166, 35, 0.5)" stroke-width="1"/>
                    <text x="170" y="25" fill="#f5a623" font-size="9" text-anchor="middle" font-weight="bold" font-family="Outfit">Straight: {details['str']}m</text>
                    
                    <!-- Off Side -->
                    <line x1="166" y1="125" x2="80" y2="125" stroke="#f5a623" stroke-width="1.5" stroke-dasharray="3"/>
                    <circle cx="80" cy="125" r="3" fill="#f5a623" />
                    <rect x="20" y="115" width="55" height="20" rx="4" fill="rgba(15, 15, 35, 0.9)" stroke="rgba(255, 255, 255, 0.15)" stroke-width="1"/>
                    <text x="47" y="128" fill="#ccd6f6" font-size="9" text-anchor="middle" font-weight="bold" font-family="Outfit">Off: {details['off']}m</text>
                    
                    <!-- Leg Side -->
                    <line x1="174" y1="125" x2="260" y2="125" stroke="#f5a623" stroke-width="1.5" stroke-dasharray="3"/>
                    <circle cx="260" cy="125" r="3" fill="#f5a623" />
                    <rect x="265" y="115" width="55" height="20" rx="4" fill="rgba(15, 15, 35, 0.9)" stroke="rgba(255, 255, 255, 0.15)" stroke-width="1"/>
                    <text x="292" y="128" fill="#ccd6f6" font-size="9" text-anchor="middle" font-weight="bold" font-family="Outfit">Leg: {details['leg']}m</text>
                </svg>
            </div>
        </div>
        """), unsafe_allow_html=True)

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
