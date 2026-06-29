"""
IPLytics Frontend — API Client

WHY THIS FILE EXISTS:
    All frontend pages need to call the FastAPI backend. Instead of
    writing requests.get() in every page, this module centralizes
    all API calls in one place.

HOW IT WORKS:
    Each function calls the backend API and returns parsed JSON.
    If the backend is down, it returns sensible defaults and shows
    an error in the UI.

WHERE IT FITS:
    Imported by every page in frontend/pages/.
"""

import logging

import requests
import streamlit as st

import os

logger = logging.getLogger(__name__)

# Use BACKEND_URL from environment for production/Docker environments, fallback to local host
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _get(endpoint: str, params: dict | None = None) -> dict | list | None:
    """
    Make a GET request to the backend API.

    Returns parsed JSON on success, None on failure.
    Displays a Streamlit error if the backend is unreachable.
    """
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    except requests.ConnectionError:
        st.error(
            "⚠️ Cannot connect to the backend server. "
            "Make sure it's running: `uvicorn backend.app.main:app --reload`"
        )
        return None

    except requests.RequestException as e:
        st.error(f"⚠️ API error: {e}")
        return None


# === Player APIs ===

def get_players(search: str | None = None) -> list[str]:
    """Get all players or search by name."""
    params = {"search": search} if search else None
    data = _get("/players", params)
    return data.get("players", []) if data else []


def get_player_stats(name: str) -> dict | None:
    """Get detailed player stats (batting + bowling + seasons)."""
    return _get(f"/players/{name}")


# === Team APIs ===

def get_teams(search: str | None = None) -> list[dict]:
    """Get all teams or search by name/abbreviation."""
    params = {"search": search} if search else None
    data = _get("/teams", params)
    return data.get("teams", []) if data else []


def get_team_stats(name: str) -> dict | None:
    """Get detailed team stats + season performance."""
    return _get(f"/teams/{name}")


# === Venue APIs ===

def get_venues(search: str | None = None) -> list[str]:
    """Get all venues or search by name."""
    params = {"search": search} if search else None
    data = _get("/venues", params)
    return data.get("venues", []) if data else []


def get_venue_stats(name: str) -> dict | None:
    """Get detailed venue stats + season scores."""
    return _get(f"/venues/{name}")


# === Comparison APIs ===

def compare_players(player1: str, player2: str) -> dict | None:
    """Compare two players side-by-side."""
    return _get("/compare/players", {"player1": player1, "player2": player2})


def compare_teams(team1: str, team2: str) -> dict | None:
    """Compare two teams with head-to-head."""
    return _get("/compare/teams", {"team1": team1, "team2": team2})


# === AI Assistant API ===

def _post(endpoint: str, json_data: dict) -> dict | None:
    """
    Make a POST request to the backend API.

    Returns parsed JSON on success, None on failure.
    Displays a Streamlit error if the backend is unreachable.
    """
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.post(url, json=json_data, timeout=60)  # AI query can be slow

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    except requests.ConnectionError:
        st.error(
            "⚠️ Cannot connect to the backend server. "
            "Make sure it's running: `uvicorn backend.app.main:app --reload`"
        )
        return None

    except requests.RequestException as e:
        st.error(f"⚠️ API error: {e}")
        return None


def ask_ai(question: str) -> dict | None:
    """Ask the AI assistant a natural language question."""
    return _post("/ai/ask", {"question": question})


# === Health Check ===

def check_health() -> bool:
    """Check if the backend is running."""
    data = _get("/health")
    return data is not None and data.get("status") == "healthy"

