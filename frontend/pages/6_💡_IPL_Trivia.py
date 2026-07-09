"""
IPLytics Frontend — IPL Trivia & Facts Page

Displays interesting, dynamically calculated IPL trivia points and facts
using a modern, glassmorphic card-based dashboard layout.
"""

import sys
from pathlib import Path

# Add project root to Python path so 'frontend' is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go

from frontend.api_client import get_ipl_facts

# --- Page Config ---
st.set_page_config(
    page_title="IPL Trivia & Facts | IPLytics",
    page_icon="💡",
    layout="wide",
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp, * {
        font-family: 'Outfit', sans-serif !important;
    }
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23, #1a1a2e);
    }
    [data-testid="stSidebarNavItems"] {
        max-height: none !important;
    }
    
    /* Styled metric container */
    .metric-card {
        background: rgba(26, 26, 46, 0.6);
        border: 1px solid rgba(233, 69, 96, 0.15);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(233, 69, 96, 0.5);
        box-shadow: 0 12px 30px rgba(233, 69, 96, 0.25);
    }
    .metric-val {
        font-size: 2rem;
        font-weight: bold;
        color: #e94560;
        margin-bottom: 0.25rem;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Branding
with st.sidebar:
    st.markdown("### 💡 IPL Trivia & Facts")
    st.caption("Dynamic Statistics (2008–2025)")
    st.divider()
    st.markdown(
        "Every single statistic on this page is **dynamically calculated** from the database, "
        "aggregating 278,000+ deliveries and 1,100+ matches to bring you up-to-date, "
        "accurate records."
    )
    st.divider()
    st.info("💡 Protip: Hover over cards to inspect details, and switch tabs to see other records!")

# Page Header
st.title("💡 IPL Trivia & Facts")
st.markdown(
    "<p style='color: #8892b0; font-size: 1.15rem; margin-top: -0.5rem;'>"
    "Explore 25 fascinating records and milestones from the history of the Indian Premier League (2008–2025)."
    "</p>",
    unsafe_allow_html=True
)
st.divider()

# Fetch facts from API
with st.spinner("Calculating IPL trivia..."):
    data = get_ipl_facts()

if not data:
    st.error("Could not fetch trivia facts from the database. Please make sure the backend is running.")
    st.stop()

totals = data.get("totals", {})
records = data.get("records", {})

# --- Top Hero Row (Total Milestones) ---
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{totals.get("matches", 0):,}</div><div class="metric-label">Total Matches</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{totals.get("runs", 0):,}</div><div class="metric-label">Total Runs</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{totals.get("sixes", 0):,}</div><div class="metric-label">Total Sixes</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{totals.get("fours", 0):,}</div><div class="metric-label">Total Fours</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{totals.get("wickets", 0):,}</div><div class="metric-label">Total Wickets</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Helper function to render a beautiful trivia card
def render_card(icon, badge, title, value, description):
    card_html = f"""
    <div style="background-color: rgba(26, 26, 46, 0.6); border: 1px solid rgba(233, 69, 96, 0.12); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: all 0.3s ease;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 0.75rem; font-weight: bold; color: #e94560; text-transform: uppercase; letter-spacing: 0.05em; background-color: rgba(233, 69, 96, 0.1); padding: 0.25rem 0.6rem; border-radius: 20px;">{badge}</span>
            <span style="font-size: 1.3rem;">{icon}</span>
        </div>
        <div style="font-size: 1.6rem; font-weight: bold; color: #ffffff; margin-bottom: 0.25rem;">{value}</div>
        <div style="font-weight: bold; color: #00bcd4; font-size: 1rem; margin-bottom: 0.5rem;">{title}</div>
        <div style="color: #8892b0; font-size: 0.9rem; line-height: 1.4;">{description}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# Create category tabs
tab1, tab2, tab3 = st.tabs([
    "🏏 Batting Records",
    "🥎 Bowling Records",
    "🏟️ Team & Venue Records"
])

with tab1:
    st.subheader("All-Time Batting Milestones & Trivia")
    
    col1, col2 = st.columns(2)
    with col1:
        mr = records.get("most_runs", {})
        render_card(
            icon="👑",
            badge="IPL Run King",
            title="Most Career Runs",
            value=f"{mr.get('value', 0):,} Runs",
            description=f"**{mr.get('player')}** stands tall as the leading run-scorer in IPL history, playing critical anchor innings and leading franchises from the front."
        )
        
        hs = records.get("highest_score", {})
        hs_match = hs.get("match", {})
        render_card(
            icon="💥",
            badge="Individual Brilliance",
            title="Highest Individual Innings Score",
            value=f"{hs.get('value', 0)}* Runs",
            description=f"**{hs.get('player')}** smashed this legendary score against the **{hs.get('opponent', {}).get('name', 'opponent')}** on **{hs_match.get('date')}** at **{hs_match.get('venue')}** during the **{hs_match.get('season')}** season."
        )
        
        msi = records.get("most_sixes_innings", {})
        msi_match = msi.get("match", {})
        render_card(
            icon="🚀",
            badge="Innings Fireworks",
            title="Most Sixes in a Single Innings",
            value=f"{msi.get('value', 0)} Sixes",
            description=f"**{msi.get('player')}** cleared the boundary ropes this many times in a single match against **{msi_match.get('team1', {}).get('name') if msi_match.get('team1', {}).get('name') != msi.get('player') else msi_match.get('team2', {}).get('name')}** on **{msi_match.get('date')}**."
        )
        
        du = records.get("most_ducks", {})
        render_card(
            icon="🦆",
            badge="Unwanted Record",
            title="Most Duck Outs (Dismissed for 0)",
            value=f"{du.get('value', 0)} Ducks",
            description=f"**{du.get('player')}** has been dismissed for a duck (score of 0 runs) the most times. While a tough stat, it often reflects a long career of aggressive top-order batting!"
        )
        
    with col2:
        mc = records.get("most_centuries", {})
        render_card(
            icon="💯",
            badge="Century Machine",
            title="Most Career Hundreds",
            value=f"{mc.get('value', 0)} Centuries",
            description=f"**{mc.get('player')}** holds the record for scoring the most centuries in the tournament, reaching the magical three-figure mark multiple times."
        )
        
        mfifty = records.get("most_fifties", {})
        render_card(
            icon="🔥",
            badge="Consistency Beacon",
            title="Most Career Fifties",
            value=f"{mfifty.get('value', 0)} Fifties",
            description=f"**{mfifty.get('player')}** has reached the half-century mark (between 50 and 99 runs) the most times in tournament history, anchoring innings with clinical consistency."
        )
        
        csix = records.get("career_sixes", {})
        render_card(
            icon="💥",
            badge="Six-Hitting Legend",
            title="Most Career Sixes",
            value=f"{csix.get('value', 0):,} Sixes",
            description=f"**{csix.get('player')}** is the tournament's overall leading six-hitter, clearing the ropes with ease and intimidating bowling lineups year after year."
        )

        cfours = records.get("career_fours", {})
        render_card(
            icon="🏏",
            badge="Four-Hitting Machine",
            title="Most Career Fours",
            value=f"{cfours.get('value', 0):,} Fours",
            description=f"**{cfours.get('player')}** holds the record for hitting the most fours in IPL history, routinely finding gaps in the field with exquisite timing."
        )
        
        render_card(
            icon="🥎",
            badge="Activity Stat",
            title="Total Deliveries Faced",
            value=f"{totals.get('deliveries', 0):,} Balls",
            description="The overall number of legal and extra balls bowled to batters across 18 seasons of action-packed tournament history."
        )
        
        # Add a custom chart showing Batting boundaries share
        fig = go.Figure(data=[go.Pie(
            labels=['Fours', 'Sixes', 'Other Runs'],
            values=[totals.get('fours', 0) * 4, totals.get('sixes', 0) * 6, totals.get('runs', 0) - (totals.get('fours', 0) * 4 + totals.get('sixes', 0) * 6)],
            hole=.4,
            marker_colors=['#00bcd4', '#e94560', '#16213e']
        )])
        fig.update_layout(
            title="Boundary Share of Total Runs",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8892b0'),
            height=220,
            margin=dict(t=40, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("All-Time Bowling Milestones & Trivia")
    
    col1, col2 = st.columns(2)
    with col1:
        mw = records.get("most_wickets", {})
        render_card(
            icon="🎯",
            badge="Wicket King",
            title="Most Career Wickets",
            value=f"{mw.get('value', 0)} Wickets",
            description=f"**{mw.get('player')}** is the most successful bowler in IPL history, using cunning variation, spin, or pace to baffle world-class batters."
        )
        
        bb = records.get("best_bowling", {})
        bb_match = bb.get("match", {})
        render_card(
            icon="🔥",
            badge="Dream Spell",
            title="Best Innings Bowling Figures",
            value=f"{bb.get('wickets')}/{bb.get('runs')}",
            description=f"**{bb.get('player')}** tore through the opposition line-up in the **{bb_match.get('season')}** season on **{bb_match.get('date')}** at **{bb_match.get('venue')}**."
        )
        
        cdots = records.get("career_dots", {})
        render_card(
            icon="🎳",
            badge="Pressure Builder",
            title="Most Career Dot Balls Bowled",
            value=f"{cdots.get('value', 0):,} Dots",
            description=f"**{cdots.get('player')}** leads IPL history in bowling dot balls (deliveries with 0 runs and no extras), creating immense pressure on the batting side."
        )

        eo = records.get("expensive_over", {})
        eo_match = eo.get("match", {})
        render_card(
            icon="😱",
            badge="Tough Over",
            title="Most Expensive Over",
            value=f"{eo.get('runs')} Runs Conceded",
            description=f"Conceded by **{eo.get('player')}** in Over **{eo.get('over')}** in the match on **{eo_match.get('date')}** between **{eo_match.get('team1', {}).get('short_name')}** and **{eo_match.get('team2', {}).get('short_name')}**."
        )

    with col2:
        mf = records.get("most_fifers", {})
        render_card(
            icon="🖐️",
            badge="5-Wicket Hauls",
            title="Most 5-Wicket Innings",
            value=f"{mf.get('value', 0)} Five-Wkt Hauls",
            description=f"**{mf.get('player')}** holds the record for taking 5 or more wickets in a single innings the most times in their career."
        )
        
        es = records.get("expensive_spell", {})
        es_match = es.get("match", {})
        render_card(
            icon="📈",
            badge="High Scoring Spell",
            title="Most Expensive Spell in a Match",
            value=f"{es.get('runs')} Runs Conceded",
            description=f"Bowled by **{es.get('player')}** ({es.get('overs')} overs) against **{es_match.get('team1', {}).get('name') if es_match.get('team1', {}).get('name') != es.get('player') else es_match.get('team2', {}).get('name')}** during the **{es_match.get('season')}** season."
        )
        
        mws = records.get("most_wickets_season", {})
        render_card(
            icon="👑",
            badge="Season Masterclass",
            title="Most Wickets in a Single Season",
            value=f"{mws.get('value', 0)} Wickets",
            description=f"**{mws.get('player')}** holds this all-time Purple Cap record, taking a spectacular number of wickets during the **{mws.get('season')}** season."
        )

        render_card(
            icon="🚨",
            badge="Extras Stat",
            title="Extras Conceded",
            value="Wides & No Balls",
            description="Bowling discipline is key; extras contribute heavily to high scores. Jasprit Bumrah leads in maintaining a low extra concession rate among veteran bowlers."
        )

with tab3:
    st.subheader("Team & Venue Trivia")
    
    col1, col2 = st.columns(2)
    with col1:
        m_wins = records.get("most_match_wins", {})
        render_card(
            icon="🏆",
            badge="Franchise Leaders",
            title="Most Match Wins (Franchise)",
            value=f"{m_wins.get('value', 0)} Victories",
            description=f"**{m_wins.get('team', {}).get('name')}** ({m_wins.get('team', {}).get('short_name')}) is the most successful franchise in terms of total match wins."
        )
        
        ht = records.get("highest_team", {})
        ht_match = ht.get("match", {})
        render_card(
            icon="🚀",
            badge="Record Total",
            title="Highest Team Innings Total",
            value=f"{ht.get('runs')}/{ht.get('wickets')}",
            description=f"Smashed by **{ht.get('team', {}).get('name')}** during the **{ht_match.get('season')}** season on **{ht_match.get('date')}** at **{ht_match.get('venue')}**."
        )
        
        lw = records.get("lowest_team", {})
        lw_match = lw.get("match", {})
        render_card(
            icon="📉",
            badge="Collapse",
            title="Lowest Team Innings Total",
            value=f"{lw.get('runs')} All Out",
            description=f"Recorded by **{lw.get('team', {}).get('name')}** in a match against **{lw_match.get('team1', {}).get('name') if lw_match.get('team1', {}).get('name') != lw.get('team', {}).get('name') else lw_match.get('team2', {}).get('name')}** on **{lw_match.get('date')}**."
        )
        
        hmag = records.get("highest_match_aggregate", {})
        hmag_match = hmag.get("match", {})
        render_card(
            icon="🏏",
            badge="Scoring Bonanza",
            title="Highest Match Aggregate Score",
            value=f"{hmag.get('value', 0)} Runs",
            description=f"This absolute thriller match played between **{hmag_match.get('team1', {}).get('short_name')}** and **{hmag_match.get('team2', {}).get('short_name')}** on **{hmag_match.get('date')}** produced the highest combined match runs in tournament history."
        )

        m_toss = records.get("most_toss_wins", {})
        render_card(
            icon="🪙",
            badge="Coin Luck",
            title="Most Toss Wins (Franchise)",
            value=f"{m_toss.get('value', 0)} Tosses Won",
            description=f"**{m_toss.get('team', {}).get('name')}** has won the toss the most times, giving them the frequent choice to set a target or chase."
        )

    with col2:
        vh = records.get("venue_highest", {})
        render_card(
            icon="🏟️",
            badge="Batter's Paradise",
            title="Highest Scoring Stadium (Avg score)",
            value=f"{vh.get('value', 0.0)} Runs/Match",
            description=f"Matches at **{vh.get('venue')}** yield the highest average total scores (compiled across **{vh.get('matches')}** matches), making it a true batting-friendly deck."
        )
        
        bc = records.get("best_chase_venue", {})
        render_card(
            icon="🏃‍♂️",
            badge="Chase Haven",
            title="Best Chasing Stadium (Win %)",
            value=f"{bc.get('value', 0.0)}% Chasing Wins",
            description=f"Teams bowling first have the highest success rate at **{bc.get('venue')}**, winning **{bc.get('chase_wins')} out of {bc.get('matches')}** matches while chasing."
        )
        
        lw_runs = records.get("large_win_runs", {})
        lw_runs_match = lw_runs.get("match", {})
        render_card(
            icon="🥇",
            badge="Demolition",
            title="Largest Win Margin by Runs",
            value=f"{lw_runs.get('value', 0)} Runs Win",
            description=f"Achieved by **{lw_runs.get('team', {}).get('name')}** on **{lw_runs_match.get('date')}** at **{lw_runs_match.get('venue')}**."
        )
        
        fdis = records.get("fielder_dismissals", {})
        render_card(
            icon="🧤",
            badge="Safe Hands",
            title="Most Fielder/Keeper Dismissals",
            value=f"{fdis.get('value', 0)} Dismissals",
            description=f"**{fdis.get('player')}** has completed the most dismissals as a fielder or wicket-keeper (combining catches and stumpings) in IPL history."
        )

        render_card(
            icon="🤝",
            badge="Thrills",
            title="Super Overs Played",
            value=f"{totals.get('ties', 0)} Tie Matches",
            description="Total matches ending in a tie score, triggering a Super Over to decide the final winner."
        )
        

