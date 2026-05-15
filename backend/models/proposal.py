"""
Proposal ORM Model for Proposal Drafter

Defines the Proposal model for the Proposal Drafter system.
"""

from typing import Any, List, Optional
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()  # type: ignore[misc]


class Proposal(Base):  # type: ignore[misc]
    """
    Proposal model representing a proposal in the Proposal Drafter system.

    Attributes:
        id: Unique UUID identifier
        user_id: Foreign key to the user who owns the proposal
        template_name: Name of the template used
        form_data: JSON data for the proposal form
        project_description: Description of the project
        generated_sections: JSON data for generated proposal sections
        reviews: JSON data for peer reviews
        is_accepted: Whether the proposal has been accepted
        status: Current status of the proposal
        contribution_id: External contribution identifier
        created_by: User who created the proposal
        updated_by: User who last updated the proposal
        template_registry_id: Foreign key to template_registry
        template_version_id: Foreign key to template_versions
        created_at: Timestamp when proposal was created
        updated_at: Timestamp when proposal was last updated
    """

    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), nullable=False)
    template_name = Column(String(255), default="proposal_template_unhcr.json")
    form_data = Column(JSON, nullable=False)
    project_description = Column(Text, nullable=False)
    generated_sections = Column(JSON, nullable=True)
    reviews = Column(JSON, nullable=True)
    is_accepted = Column(Boolean, default=False)
    status = Column(String, default="draft")
    contribution_id = Column(String, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Template registry/version tracking
    template_registry_id = Column(UUID(as_uuid=True), nullable=True)
    template_version_id = Column(UUID(as_uuid=True), nullable=True)

    # Note: In the database schema, there's no explicit owner_id column for proposals.
    # The user_id column serves as the owner. We add a property for compatibility.
    @property
    def owner_id(self) -> Optional[str]:
        """Get the owner ID (aliases user_id for compatibility)."""
        return str(self.user_id) if self.user_id else None

    @property
    def team_id(self) -> Optional[str]:
        """
        Get the team ID associated with this proposal.

        Note: The proposals table doesn't have a team_id column in the schema.
        This is a placeholder that would need to be populated based on the user's team
        or through a separate mapping table.
        """
        # This would need to be implemented based on actual schema
        # For now, return None as it's not in the current schema
        return None

    @property
    def donor_group_id(self) -> Optional[str]:
        """
        Get the donor group ID associated with this proposal.

        Note: The proposals table doesn't have a donor_group_id column.
        This is a placeholder.
        """
        return None

    def __repr__(self):
        return f"<Proposal(id={self.id}, user_id={self.user_id}, status='{self.status}')>"

    @classmethod
    def get_by_id(cls, session, proposal_id: Any) -> Optional["Proposal"]:
        """Get a proposal by its ID."""
        return session.query(cls).filter_by(id=proposal_id).first()

    @classmethod
    def get_by_owner(cls, session, owner_id: str) -> List["Proposal"]:
        """Get all proposals owned by a user."""
        return session.query(cls).filter_by(user_id=owner_id).all()
