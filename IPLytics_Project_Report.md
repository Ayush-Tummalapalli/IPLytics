# IPLytics: AI-Powered IPL Cricket Analytics Platform
## Project Report & Technical Documentation

---

### 1. Project Overview
**IPLytics** is an advanced, data-driven analytics platform designed for the Indian Premier League (IPL) cricket tournament. It processes real-world match and ball-by-ball delivery datasets spanning from **2008 to 2025** to compute comprehensive, career-level analytics. Additionally, it integrates a Retrieval-Augmented Generation (RAG) AI Assistant powered by **Google Gemini** to allow natural language queries about tournament history, player statistics, and stadium trends.

- **Frontend Tech Stack:** Python, Streamlit, Plotly (dynamic charts)
- **Backend Tech Stack:** FastAPI, SQLAlchemy (ORM), Pydantic
- **Database:** PostgreSQL (locally hosted)
- **AI Integration:** Google GenAI SDK (Gemini 2.5 Flash)

---

### 2. System Architecture
IPLytics uses a decoupled model-view-controller (MVC) inspired architecture:

```
                  ┌──────────────────────────────┐
                  │      Streamlit Frontend      │
                  └──────────────┬───────────────┘
                                 │ HTTP requests
                                 ▼
                  ┌──────────────────────────────┐
                  │       FastAPI Backend        │
                  └──────────────┬───────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
        ┌─────────────────────┐     ┌─────────────────────┐
        │    PostgreSQL DB    │     │  Google Gemini API  │
        └─────────────────────┘     └─────────────────────┘
```

1. **Database Layer:** Manages 4 core relational tables: `teams`, `players`, `matches`, and `deliveries`.
2. **Analytics Service (Backend):** Compiles career-level batting/bowling statistics, head-to-head records, venue-level scoring trends, and win-loss breakdowns using SQL-level database aggregations.
3. **RAG Service (AI Assistant):** Translates user natural language questions into database context, appending structured statistics to Gemini prompts to deliver data-backed, hallucination-free cricket insights.
4. **Presentation Layer (Frontend):** Renders premium visual dashboards, side-by-side player/team comparisons, and an interactive chat interface.

---

### 3. Database Schema & Ingestion Pipeline
The database is loaded from a consolidated real-world dataset (`IPL.csv`) containing complete matches and deliveries up to the 2025 season:
- **Teams Table:** Stores 15 canonical IPL franchises. The ingestion pipeline implements an alias mapping that automatically maps all 19 raw team names from historical data (e.g. `Delhi Daredevils` -> `Delhi Capitals`, `Kings XI Punjab` -> `Punjab Kings`) to their canonical forms.
- **Players Table:** Stores 767 unique player profiles extracted from the ball-by-ball deliveries data.
- **Matches Table:** Stores 1,169 match-level records, including season calendar years (parsed from mixed formats like `'2007/08'`, `'2020/21'`), toss decisions, win margins, and Duckworth-Lewis-Stern flags.
- **Deliveries Table:** Stores 278,205 ball-by-ball records, including run breakdowns, extras types, and wicket details.

---

### 4. Key Analytical Enhancements & Corrections
To ensure the integrity of the displayed records, several math formulas and logic constraints were implemented:
1. **Bowling Economy Rate:** Calculated using exact legal deliveries faced: `(runs_conceded * 6) / legal_balls` instead of integer division of completed overs.
2. **Bowler-Credited Wickets:** Excludes non-bowler dismissals (e.g., `run out`, `retired hurt`, `retired out`, `obstructing the field`) when calculating bowler averages and wicket tallies.
3. **Batting Average:** Excludes `retired hurt` innings from dismissals in the denominator to avoid penalizing players for retiring due to injuries.
4. **Bat-First vs Chase Wins:** Explicitly determines bat-first wins using the logic: `won_toss AND toss_decision == 'bat'` OR `lost_toss AND toss_decision == 'field'`. This guarantees `Bat First Wins` + `Chase Wins` == `Total Wins` for all franchises.

---

### 5. Interactive Features
*   **Player Analytics:** Visualizes career summaries, boundaries, strike rate trends, and lists all historical franchises the selected player has represented.
*   **Team Analytics:** Computes win percentages, home/away splits, win method breakdowns, and season-by-season wins vs. losses.
*   **Venue Analytics:** Highlights average first/second innings scores, chase success rates, and highest/lowest team totals.
*   **Side-by-Side Comparisons:** Allows direct comparison of two players (batting and bowling metrics side-by-side using Plotly charts) or two teams (head-to-head matches).
*   **IPLytics AI (RAG Assistant):** Utilizes dynamic context injection. For comparative or year-specific queries (e.g., `"Which venue has the highest average score?"` or `"2025?"`), it pulls top-level database summaries (top run-scorers, top wicket-takers, highest-scoring venues, and season winners history) into the prompt context for Gemini.

---

### 6. Sample Project Statistics (Verified)
- **Mumbai Indians (MI) Career Stats:** 277 matches, 151 wins, 122 losses, 4 no-results. Bat First Wins: 76, Chase Wins: 75.
- **Jasprit Bumrah (JJ Bumrah) Bowling Stats:** 145 matches, 186 wickets, 559.5 overs bowled, 4,162 runs conceded. **Economy:** 7.43, **Average:** 22.38, **Best Figures:** 5/10.
- **Virat Kohli (V Kohli) Batting Stats:** 8,671 total runs.
- **2025 IPL Champions:** Royal Challengers Bengaluru (RCB) defeated Punjab Kings (PBKS) in the final on June 3, 2025.
