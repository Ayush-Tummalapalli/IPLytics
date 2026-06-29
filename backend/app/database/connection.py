"""
IPLytics — Database Connection & Session Management

WHY THIS FILE EXISTS:
    Every time we need to read or write data from PostgreSQL, we need
    a "session" — a temporary connection to the database. This module
    sets up:
    1. The Engine — manages the actual connection pool to PostgreSQL
    2. SessionLocal — a factory that creates new sessions on demand
    3. get_db() — a FastAPI dependency that provides a session to each
       API request and auto-closes it when the request is done

HOW IT WORKS:
    SQLAlchemy uses a pattern called "Unit of Work". Each session
    tracks all changes you make (inserts, updates, deletes) and
    sends them to the database in a single transaction when you
    call commit().

    The get_db() function uses Python's "yield" to:
    1. Create a session before the API handler runs
    2. Give it to the handler to use
    3. Close it after the handler finishes (even if there's an error)

    This is called "dependency injection" — FastAPI handles the
    lifecycle automatically.

WHERE IT FITS:
    - Imported by API routes to get database sessions
    - Imported by create_db.py to create tables
    - Imported by the ETL pipeline (Phase 3) for data ingestion
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import settings
from backend.app.models.base import Base

logger = logging.getLogger(__name__)

# --- Engine ---
# The engine manages a pool of database connections.
# echo=True logs all SQL queries (useful for debugging, disable in production)
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Test connections before using them (handles DB restarts)
)

# --- Session Factory ---
# Creates new Session objects. Each session is a "workspace" for DB operations.
# autocommit=False: We manually control when changes are saved
# autoflush=False: We manually control when SQLAlchemy syncs with the DB
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Usage in a route:
        @app.get("/players")
        def get_players(db: Session = Depends(get_db)):
            return db.query(Player).all()

    The session is automatically closed when the request finishes,
    even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Create all database tables defined by SQLAlchemy models.

    This reads the Base.metadata (which knows about all models
    that inherit from Base) and creates any tables that don't
    exist yet in the database. It will NOT modify existing tables.
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully.")


def drop_tables() -> None:
    """
    Drop all database tables. USE WITH CAUTION.

    This is useful during development to reset the database.
    Never call this in production.
    """
    logger.warning("⚠️ Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped.")
