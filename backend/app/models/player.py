"""
IPLytics — Player Model

WHY THIS FILE EXISTS:
    The players table stores unique player names extracted from
    the deliveries data. Since the Kaggle dataset doesn't include
    player metadata (age, role, nationality, etc.), we only store
    the name as it appears in the CSV.

    This table serves as a lookup/reference for:
    - Player analytics queries
    - Search/autocomplete on the frontend
    - AI assistant entity extraction

HOW IT WORKS:
    - `id`: Auto-incrementing primary key
    - `name`: The player name as it appears in the dataset (unique)

    During data ingestion (Phase 3), we'll extract unique player
    names from the batter, bowler, and fielder columns in deliveries.csv.

WHERE IT FITS:
    One of the 4 core ORM models. Referenced by analytics queries
    but NOT by foreign keys from deliveries (player names in
    deliveries are stored as strings to handle CSV inconsistencies).
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Player(Base):
    """Represents an IPL player."""

    __tablename__ = "players"

    # --- Columns ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, name='{self.name}')>"
