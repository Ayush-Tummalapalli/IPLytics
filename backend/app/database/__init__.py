"""
IPLytics Backend — Database Connection & Session Management.

Import database utilities from a single location:
    from backend.app.database import get_db, create_tables, engine
"""

from backend.app.database.connection import (
    engine,
    SessionLocal,
    get_db,
    create_tables,
    drop_tables,
)

__all__ = ["engine", "SessionLocal", "get_db", "create_tables", "drop_tables"]
