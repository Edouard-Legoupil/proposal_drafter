"""
SQLAlchemy ORM Models for Proposal Drafter

This module provides SQLAlchemy ORM models that map to the PostgreSQL database.
These models are used for object-level authorization checks and database operations.

Note: This project uses sync SQLAlchemy (not async) with the existing get_engine()
from backend.core.db. All models are designed to work with sync database connections.

Available models:
- User: User model with authorization methods
- Proposal: Proposal model
- KnowledgeCard: Knowledge card model
- Template: Template model
- Team: Team model
- TeamMember: Team membership model
- DonorGroupMember: Donor group membership model
- Role: Role model
- UserRole: User-Role many-to-many relationship
"""

from backend.models.user import User
from backend.models.proposal import Proposal
from backend.models.knowledge_card import KnowledgeCard
from backend.models.template import Template
from backend.models.team import Team, TeamMember
from backend.models.donor_group import DonorGroupMember
from backend.models.role import Role, UserRole

__all__ = [
    "User",
    "Proposal",
    "KnowledgeCard",
    "Template",
    "Team",
    "TeamMember",
    "DonorGroupMember",
    "Role",
    "UserRole",
]
