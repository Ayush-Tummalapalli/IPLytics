"""
IPLytics — Match Model

WHY THIS FILE EXISTS:
    The matches table stores match-level data — one row per IPL match.
    This includes teams, venue, toss, result, and winner information.
    It maps directly to matches.csv from the Kaggle dataset.

HOW IT WORKS:
    Each match references the teams table through foreign keys:
    - team1_id, team2_id: The two teams playing
    - toss_winner_id: Who won the toss
    - winner_id: Who won the match (nullable for ties/no results)

    Indexes are placed on columns frequently used in WHERE clauses
    and JOINs for analytics queries (season, venue, team IDs).

WHERE IT FITS:
    One of the 4 core ORM models. Referenced by deliveries (via
    match_id FK) and used heavily by the analytics engine for
    team performance, venue analysis, and season trends.
"""

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class Match(Base):
    """Represents a single IPL match."""

    __tablename__ = "matches"

    # --- Primary Key ---
    # We use the match ID from the CSV (not auto-increment) so it
    # matches the match_id column in deliveries.csv
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- Match Context ---
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    venue: Mapped[str] = mapped_column(String(200), nullable=False)

    # --- Teams (Foreign Keys) ---
    team1_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )
    team2_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )

    # --- Toss ---
    toss_winner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )
    toss_decision: Mapped[str] = mapped_column(String(10), nullable=False)

    # --- Result ---
    winner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=True  # Null for tie/no result
    )
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    win_by_runs: Mapped[int] = mapped_column(Integer, default=0)
    win_by_wickets: Mapped[int] = mapped_column(Integer, default=0)
    player_of_match: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # --- Additional ---
    dl_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    target_runs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_overs: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Relationships ---
    team1 = relationship("Team", foreign_keys=[team1_id], back_populates="matches_as_team1")
    team2 = relationship("Team", foreign_keys=[team2_id], back_populates="matches_as_team2")
    toss_winner = relationship("Team", foreign_keys=[toss_winner_id])
    winner = relationship("Team", foreign_keys=[winner_id], back_populates="matches_won")
    deliveries = relationship("Delivery", back_populates="match", cascade="all, delete-orphan")

    # --- Indexes ---
    # These speed up common analytics queries
    __table_args__ = (
        Index("ix_matches_season", "season"),
        Index("ix_matches_venue", "venue"),
        Index("ix_matches_team1_id", "team1_id"),
        Index("ix_matches_team2_id", "team2_id"),
        Index("ix_matches_winner_id", "winner_id"),
    )

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, season={self.season}, venue='{self.venue}')>"
