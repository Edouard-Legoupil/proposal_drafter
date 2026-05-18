"""
User Association ORM Models for Proposal Drafter

Defines association models for many-to-many relationships between users and various entities.
"""

from typing import List
from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

# Type alias for mypy - this is the proper way to handle SQLAlchemy declarative base
Base = declarative_base()  # type: ignore[valid-type]


class UserOutcome(Base):  # type: ignore[valid-type, misc]
    """
    Association table for the many-to-many relationship between Users and Outcomes.

    Attributes:
        user_id: Foreign key to users table
        outcome_id: Foreign key to outcomes table
    """

    __tablename__ = "user_outcomes"

    user_id = Column(String, primary_key=True, nullable=False)
    outcome_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)

    def __repr__(self):
        return f"<UserOutcome(user_id={self.user_id}, outcome_id={self.outcome_id})>"

    @classmethod
    def get_user_outcomes(cls, session, user_id: str) -> List[str]:
        """Get all outcome IDs for a specific user."""
        results = session.query(cls).filter_by(user_id=user_id).all()
        return [str(outcome.outcome_id) for outcome in results]


class UserFieldContext(Base):  # type: ignore[valid-type, misc]
    """
    Association table for the many-to-many relationship between Users and Field Contexts.

    Attributes:
        user_id: Foreign key to users table
        field_context_id: Foreign key to field_contexts table
    """

    __tablename__ = "user_field_contexts"

    user_id = Column(String, primary_key=True, nullable=False)
    field_context_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)

    def __repr__(self):
        return f"<UserFieldContext(user_id={self.user_id}, field_context_id={self.field_context_id})>"

    @classmethod
    def get_user_field_contexts(cls, session, user_id: str) -> List[str]:
        """Get all field context IDs for a specific user."""
        results = session.query(cls).filter_by(user_id=user_id).all()
        return [str(fc.field_context_id) for fc in results]


# Import UUID for type hints
from uuid import UUID
