"""
IPLytics — Database Table Creation Script

WHY THIS FILE EXISTS:
    This is a standalone script you run ONCE to create all the
    database tables in PostgreSQL. It reads the SQLAlchemy models
    and creates matching tables in your database.

HOW TO RUN:
    From the project root directory:
        python -m backend.app.database.create_db

    Before running, make sure:
    1. PostgreSQL is running
    2. The 'iplytics' database exists
    3. Your .env file has the correct DATABASE_URL

WHAT IT DOES:
    1. Imports all model files (Team, Player, Match, Delivery)
       so SQLAlchemy's Base.metadata knows about them
    2. Calls create_tables() which runs CREATE TABLE IF NOT EXISTS
       for each model
    3. Logs success or failure

WHERE IT FITS:
    Run this once after setting up the database.
    Run it again if you add new models (it won't break existing tables).
"""

import logging
import sys

# Configure logging before any other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Create all database tables."""
    try:
        # Import all models so Base.metadata knows about them.
        # These imports register each model's table with Base.metadata.
        # Without these imports, create_tables() would create nothing.
        from backend.app.models.team import Team  # noqa: F401
        from backend.app.models.player import Player  # noqa: F401
        from backend.app.models.match import Match  # noqa: F401
        from backend.app.models.delivery import Delivery  # noqa: F401

        logger.info("All models imported: Team, Player, Match, Delivery")

        # Create tables
        from backend.app.database.connection import create_tables
        create_tables()

        logger.info("🏏 IPLytics database setup complete!")
        logger.info("Tables created: teams, players, matches, deliveries")

    except Exception as e:
        logger.error("❌ Failed to create database tables: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
