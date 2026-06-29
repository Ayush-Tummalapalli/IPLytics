"""
IPLytics — Delivery Model

WHY THIS FILE EXISTS:
    The deliveries table stores ball-by-ball data — one row per delivery
    bowled in every IPL match. This is the largest table (~250,000+ rows)
    and the primary source for player analytics (runs, strike rates,
    wickets, etc.).

HOW IT WORKS:
    Each delivery belongs to a match (via match_id FK) and references
    teams (via batting_team_id, bowling_team_id FKs).

    Player names (batter, bowler, fielder) are stored as strings rather
    than foreign keys to the players table. This is a deliberate design
    choice because:
    1. CSV data has inconsistent player naming
    2. Avoids FK constraint failures during bulk data ingestion
    3. We can still JOIN with the players table using name matching

    Indexes are placed on columns used in GROUP BY and WHERE clauses
    for analytics (batter, bowler, match_id, batting_team_id).

WHERE IT FITS:
    One of the 4 core ORM models. This is the most queried table —
    all player statistics (runs, averages, strike rates) and most
    team statistics are computed from aggregations on this table.
"""

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class Delivery(Base):
    """Represents a single ball bowled in an IPL match."""

    __tablename__ = "deliveries"

    # --- Primary Key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Match Reference ---
    match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matches.id"), nullable=False
    )
    innings: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Ball Info ---
    over: Mapped[int] = mapped_column(Integer, nullable=False)
    ball: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Teams (Foreign Keys) ---
    batting_team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )
    bowling_team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )

    # --- Players (stored as strings, not FKs — see module docstring) ---
    batter: Mapped[str] = mapped_column(String(100), nullable=False)
    non_striker: Mapped[str] = mapped_column(String(100), nullable=False)
    bowler: Mapped[str] = mapped_column(String(100), nullable=False)

    # --- Runs ---
    runs_batter: Mapped[int] = mapped_column(Integer, nullable=False)
    runs_extras: Mapped[int] = mapped_column(Integer, nullable=False)
    runs_total: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Extras Detail ---
    extra_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # --- Wicket ---
    wicket_kind: Mapped[str | None] = mapped_column(String(30), nullable=True)
    player_dismissed: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fielder: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # --- Relationships ---
    match = relationship("Match", back_populates="deliveries")
    batting_team = relationship("Team", foreign_keys=[batting_team_id])
    bowling_team = relationship("Team", foreign_keys=[bowling_team_id])

    # --- Indexes ---
    # These speed up common analytics queries
    __table_args__ = (
        Index("ix_deliveries_match_id", "match_id"),
        Index("ix_deliveries_batter", "batter"),
        Index("ix_deliveries_bowler", "bowler"),
        Index("ix_deliveries_batting_team_id", "batting_team_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Delivery(match_id={self.match_id}, innings={self.innings}, "
            f"over={self.over}, ball={self.ball}, batter='{self.batter}')>"
        )
