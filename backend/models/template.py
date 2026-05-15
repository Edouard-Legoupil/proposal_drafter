"""
Template ORM Model for Proposal Drafter

Defines the Template model for the Proposal Drafter system.
"""

from typing import Any, List, Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, Boolean, DateTime, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()  # type: ignore[misc]


# Enums for template types and statuses
class TemplateType(str, PyEnum):
    proposal = "proposal"
    concept_note = "concept_note"
    knowledge_card = "knowledge_card"


class TemplateStatus(str, PyEnum):
    draft = "draft"
    active = "active"
    deprecated = "deprecated"
    archived = "archived"


class Template(Base):
    """
    Template model representing a template in the Proposal Drafter system.

    Attributes:
        id: Unique UUID identifier
        name: Name of the template
        filename: Filename of the template
        template_type: Type of template (proposal, concept_note, knowledge_card)
        description: Description of the template
        status: Current status of the template
        is_default: Whether this is the default template for its type
        created_by: User who created the template
        updated_by: User who last updated the template
        created_at: Timestamp when template was created
        updated_at: Timestamp when template was last updated
    """

    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False, unique=True)
    template_type = Column(String, nullable=False)  # Store as string, not enum for simplicity
    description = Column(Text, nullable=True)
    status = Column(String, default="draft")  # Store as string, not enum for simplicity
    is_default = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Note: In the database schema, there's no explicit owner_id column.
    # The created_by column serves as the owner.
    @property
    def owner_id(self) -> Optional[str]:
        """Get the owner ID (aliases created_by for compatibility)."""
        return str(self.created_by) if self.created_by else None

    @property
    def team_id(self) -> Optional[str]:
        """Get the team ID associated with this template."""
        # Not in current schema - placeholder
        return None

    @property
    def organization_id(self) -> Optional[str]:
        """Get the organization ID associated with this template."""
        # Not in current schema - placeholder
        return None

    @property
    def donor_group_id(self) -> Optional[str]:
        """Get the donor group ID associated with this template."""
        # Not in current schema - placeholder
        return None

    @property
    def is_public(self) -> bool:
        """Check if this template is public."""
        # Not in current schema - placeholder
        return False

    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}', template_type={self.template_type})>"

    @classmethod
    def get_by_id(cls, session, template_id: Any) -> Optional["Template"]:
        """Get a template by its ID."""
        return session.query(cls).filter_by(id=template_id).first()

    @classmethod
    def get_by_owner(cls, session, owner_id: str) -> List["Template"]:
        """Get all templates owned by a user."""
        return session.query(cls).filter_by(created_by=owner_id).all()

    @classmethod
    def get_default(cls, session, template_type: str) -> Optional["Template"]:
        """Get the default template for a given type."""
        return session.query(cls).filter_by(template_type=template_type, is_default=True).first()
