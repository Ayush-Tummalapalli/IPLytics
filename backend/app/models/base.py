"""
IPLytics — SQLAlchemy Declarative Base

WHY THIS FILE EXISTS:
    Every SQLAlchemy model (Team, Player, Match, Delivery) needs to
    inherit from the same Base class. This Base holds a single
    MetaData object that knows about ALL tables. When we call
    Base.metadata.create_all(engine), it creates every table that
    any model has registered.

    By putting Base in its own file, we avoid circular imports.
    Models can import Base without importing each other.

HOW IT WORKS:
    DeclarativeBase is SQLAlchemy 2.0's modern way to create the
    base class. All models inherit from it and automatically
    register their table definitions.

WHERE IT FITS:
    This is imported by every model file (team.py, player.py, etc.)
    and by the database connection module (to create/drop tables).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass
