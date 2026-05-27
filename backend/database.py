"""
Database module for async session management.

This module provides the async_session_maker for database operations.
"""

from sqlalchemy.orm import sessionmaker
from backend.core.db import get_engine, engine

# Create async session maker
async_session_maker = sessionmaker(bind=engine, expire_on_commit=False)  # type: ignore[name-defined]