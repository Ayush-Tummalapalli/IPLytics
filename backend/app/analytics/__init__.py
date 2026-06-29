"""
IPLytics Backend — Core Analytics Functions.

Import analytics services from a single location:
    from backend.app.analytics import player_analytics, team_analytics, venue_analytics
"""

from backend.app.analytics import player_analytics
from backend.app.analytics import team_analytics
from backend.app.analytics import venue_analytics

__all__ = ["player_analytics", "team_analytics", "venue_analytics"]
