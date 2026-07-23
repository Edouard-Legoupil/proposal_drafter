"""
Team ORM Model for Proposal Drafter

Defines the Team and TeamMember models for team-based access control.
"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy import Integer  # type: ignore[import]
from sqlalchemy.orm import relationship

# Import shared base from models package to ensure all models share the same registry
# This fixes cross-model relationship resolution issues
from backend.models import Base  # type: ignore[valid-type]


class Team(Base):  # type: ignore[valid-type, misc]
    """
    Team model representing a team in the Proposal Drafter system.

    Attributes:
        id: Unique UUID identifier for the team
        name: Name of the team (unique)
        members: Relationship to team members
        proposals: Relationship to proposals owned by this team
    """

    __tablename__ = "teams"

    id = Column(String, primary_key=True, nullable=False)
    name = Column(String, unique=True, nullable=False, index=True)

    # Relationships
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    team_roles = relationship("TeamRole", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

    @classmethod
    def get_by_name(cls, session, name: str):
        """Get a team by its name."""
        return session.query(cls).filter_by(name=name).first()


class TeamRole(Base):  # type: ignore[valid-type, misc]
    """
    Association table for the many-to-many relationship between Teams and Roles.

    Attributes:
        team_id: Foreign key to teams table
        role_id: Foreign key to roles table
        team: Relationship to Team
        role: Relationship to Role
    """

    __tablename__ = "team_roles"

    team_id = Column(String, ForeignKey("teams.id"), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True, nullable=False)

    # Relationships
    team = relationship("Team", back_populates="team_roles")
    role = relationship("Role", back_populates="team_roles")

    def __repr__(self):
        return f"<TeamRole(team_id={self.team_id}, role_id={self.role_id})>"

    @classmethod
    def get_team_roles(cls, session, team_id: str) -> list:
        """Get all roles for a team."""
        return session.query(cls).filter_by(team_id=team_id).all()

    @classmethod
    def has_role(cls, session, team_id: str, role_id: int) -> bool:
        """Check if a team has a specific role."""
        return session.query(cls).filter_by(team_id=team_id, role_id=role_id).first() is not None


class TeamMember(Base):  # type: ignore[valid-type, misc]
    """
    Association table for the many-to-many relationship between Users and Teams.

    Attributes:
        team_id: Foreign key to teams table
        user_id: Foreign key to users table
        status: Membership status (PENDING, ACTIVE, REJECTED)
        team: Relationship to Team
        user: Relationship to User
    """

    __tablename__ = "team_members"

    team_id = Column(String, ForeignKey("teams.id"), primary_key=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)

    # Relationships
    team = relationship("Team", back_populates="members")
    # Note: user relationship is defined in User model to avoid circular imports

    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, status={self.status})>"

    @classmethod
    def is_member(cls, session, team_id: str, user_id: str) -> bool:
        """Check if a user is a member of a team."""
        return session.query(cls).filter_by(team_id=team_id, user_id=user_id).first() is not None

    @classmethod
    def is_active_member(cls, session, team_id: str, user_id: str) -> bool:
        """Check if a user is an active member of a team."""
        return session.query(cls).filter_by(team_id=team_id, user_id=user_id, status="ACTIVE").first() is not None

    @classmethod
    def get_membership_status(cls, session, team_id: str, user_id: str) -> str:
        """Get the membership status of a user in a team."""
        membership = session.query(cls).filter_by(team_id=team_id, user_id=user_id).first()
        return membership.status if membership else "NOT_MEMBER"

    @classmethod
    def get_pending_requests(cls, session, team_id: str) -> list:
        """Get all pending membership requests for a team."""
        return session.query(cls).filter_by(team_id=team_id, status="PENDING").all()
