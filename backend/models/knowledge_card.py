"""
Knowledge Card ORM Model for Proposal Drafter

Defines the KnowledgeCard model for the Proposal Drafter system.
"""

from typing import Any, List, Optional
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()  # type: ignore[misc]


class KnowledgeCard(Base):
    """
    KnowledgeCard model representing a knowledge card in the Proposal Drafter system.

    Attributes:
        id: Unique UUID identifier
        template_name: Name of the template used
        type: Type of knowledge card
        summary: Summary of the knowledge card
        generated_sections: JSON data for generated sections
        is_accepted: Whether the knowledge card has been accepted
        status: Current status of the knowledge card
        donor_id: Foreign key to donor (if applicable)
        outcome_id: Foreign key to outcome (if applicable)
        field_context_id: Foreign key to field context (if applicable)
        created_by: User who created the knowledge card
        updated_by: User who last updated the knowledge card
        template_registry_id: Foreign key to template_registry
        template_version_id: Foreign key to template_versions
        created_at: Timestamp when knowledge card was created
        updated_at: Timestamp when knowledge card was last updated
    """

    __tablename__ = "knowledge_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    template_name = Column(String, nullable=True)
    type = Column(String, nullable=True)
    summary = Column(Text, nullable=False)
    generated_sections = Column(JSON, nullable=True)
    is_accepted = Column(Boolean, default=False)
    status = Column(String, default="draft")
    donor_id = Column(UUID(as_uuid=True), nullable=True)
    outcome_id = Column(UUID(as_uuid=True), nullable=True)
    field_context_id = Column(UUID(as_uuid=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Template registry/version tracking
    template_registry_id = Column(UUID(as_uuid=True), nullable=True)
    template_version_id = Column(UUID(as_uuid=True), nullable=True)

    # Note: In the database schema, there's no explicit owner_id column.
    # The created_by column serves as the owner.
    @property
    def owner_id(self) -> Optional[str]:
        """Get the owner ID (aliases created_by for compatibility)."""
        return str(self.created_by) if self.created_by else None

    @property
    def team_id(self) -> Optional[str]:
        """Get the team ID associated with this knowledge card."""
        # Not in current schema - placeholder
        return None

    @property
    def donor_group_id(self) -> Optional[str]:
        """Get the donor group ID associated with this knowledge card."""
        # Not in current schema - placeholder
        return None

    @property
    def shared_with(self) -> List[str]:
        """Get list of user IDs this knowledge card is shared with."""
        # This would need to be implemented based on actual sharing mechanism
        return []

    def __repr__(self):
        return f"<KnowledgeCard(id={self.id}, created_by={self.created_by}, status='{self.status}')>"

    @classmethod
    def get_by_id(cls, session, knowledge_card_id: Any) -> Optional["KnowledgeCard"]:
        """Get a knowledge card by its ID."""
        return session.query(cls).filter_by(id=knowledge_card_id).first()

    @classmethod
    def get_by_owner(cls, session, owner_id: str) -> List["KnowledgeCard"]:
        """Get all knowledge cards owned by a user."""
        return session.query(cls).filter_by(created_by=owner_id).all()
