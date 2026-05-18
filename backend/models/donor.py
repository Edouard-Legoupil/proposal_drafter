"""
Donor ORM Model for Proposal Drafter

Defines the Donor model for managing donor information.
"""

from typing import Any, Optional, List
from sqlalchemy import Column, String, func, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

# Type alias for mypy - this is the proper way to handle SQLAlchemy declarative base
Base = declarative_base()  # type: ignore[valid-type]


class Donor(Base):  # type: ignore[valid-type, misc]
    """
    Donor model representing donor organizations in the system.

    Attributes:
        id: Unique UUID identifier
        account_id: External account identifier
        name: Name of the donor organization
        country: Country of the donor
        donor_group: Group/category the donor belongs to
        created_by: User who created the donor record
        created_at: Timestamp when donor was created
        last_updated: Timestamp when donor was last updated
    """

    __tablename__ = "donors"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    account_id = Column(String, unique=True, nullable=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    country = Column(String(100), nullable=True)
    donor_group = Column(String(100), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    # Note: Relationships would be defined here if there are direct relationships
    # For example: proposals = relationship("Proposal", back_populates="donor")

    def __repr__(self):
        return f"<Donor(id={self.id}, name='{self.name}')>"

    @classmethod
    def get_by_id(cls, session, donor_id: Any) -> Optional["Donor"]:
        """Get a donor by its ID."""
        return session.query(cls).filter_by(id=donor_id).first()

    @classmethod
    def get_by_name(cls, session, name: str) -> Optional["Donor"]:
        """Get a donor by its name."""
        return session.query(cls).filter_by(name=name).first()

    @classmethod
    def get_all(cls, session) -> List["Donor"]:
        """Get all donors."""
        return session.query(cls).order_by(cls.name).all()

    @classmethod
    def get_by_group(cls, session, donor_group: str) -> List["Donor"]:
        """Get all donors in a specific group."""
        return session.query(cls).filter_by(donor_group=donor_group).order_by(cls.name).all()

    @classmethod
    def get_distinct_groups(cls, session) -> List[str]:
        """Get all distinct donor groups."""
        results = session.query(cls.donor_group.distinct()).order_by(cls.donor_group).all()
        return [group[0] for group in results if group[0] is not None]


class Outcome(Base):  # type: ignore[valid-type, misc]
    """
    Outcome model representing project outcomes in the system.

    Attributes:
        id: Unique UUID identifier
        name: Name/description of the outcome
        created_by: User who created the outcome
        created_at: Timestamp when outcome was created
    """

    __tablename__ = "outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    # Note: Relationships would be defined here if there are direct relationships

    def __repr__(self):
        return f"<Outcome(id={self.id}, name='{self.name}')>"

    @classmethod
    def get_by_id(cls, session, outcome_id: Any) -> Optional["Outcome"]:
        """Get an outcome by its ID."""
        return session.query(cls).filter_by(id=outcome_id).first()

    @classmethod
    def get_by_name(cls, session, name: str) -> Optional["Outcome"]:
        """Get an outcome by its name."""
        return session.query(cls).filter_by(name=name).first()

    @classmethod
    def get_all(cls, session) -> List["Outcome"]:
        """Get all outcomes."""
        return session.query(cls).order_by(cls.name).all()


# Import DateTime for type hints
