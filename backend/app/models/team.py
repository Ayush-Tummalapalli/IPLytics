"""
IPLytics — Team Model

WHY THIS FILE EXISTS:
    The teams table stores canonical IPL team names. This is important
    because team names have changed over the years:
        - "Delhi Daredevils" → "Delhi Capitals" (2019)
        - "Deccan Chargers" → "Sunrisers Hyderabad" (2013)
        - "Kings XI Punjab" → "Punjab Kings" (2021)

    Having a teams table lets us map these variations to a single
    canonical entry during data ingestion (Phase 3).

HOW IT WORKS:
    - `id`: Auto-incrementing primary key
    - `name`: The canonical team name (unique, required)
    - `short_name`: Optional abbreviation like "MI", "CSK", "RCB"

    Relationships:
    - matches reference teams via team1_id, team2_id, winner_id, etc.
    - deliveries reference teams via batting_team_id, bowling_team_id

WHERE IT FITS:
    This is one of the 4 core ORM models. It's referenced by both
    the Match and Delivery models through foreign keys.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class Team(Base):
    """Represents an IPL team."""

    __tablename__ = "teams"

    # --- Columns ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # --- Relationships ---
    # Matches where this team played as team1
    matches_as_team1 = relationship(
        "Match", foreign_keys="Match.team1_id", back_populates="team1"
    )
    # Matches where this team played as team2
    matches_as_team2 = relationship(
        "Match", foreign_keys="Match.team2_id", back_populates="team2"
    )
    # Matches won by this team
    matches_won = relationship(
        "Match", foreign_keys="Match.winner_id", back_populates="winner"
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}')>"
