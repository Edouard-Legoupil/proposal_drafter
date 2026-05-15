"""
Team ORM Model for Proposal Drafter

Defines the Team and TeamMember models for team-based access control.
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()  # type: ignore[misc]


class Team(Base):  # type: ignore[misc]
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

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

    @classmethod
    def get_by_name(cls, session, name: str):
        """Get a team by its name."""
        return session.query(cls).filter_by(name=name).first()


class TeamMember(Base):  # type: ignore[misc]
    """
    Association table for the many-to-many relationship between Users and Teams.

    Attributes:
        team_id: Foreign key to teams table
        user_id: Foreign key to users table
        team: Relationship to Team
        user: Relationship to User
    """

    __tablename__ = "team_members"

    team_id = Column(String, primary_key=True, nullable=False)
    user_id = Column(String, primary_key=True, nullable=False)

    # Relationships
    team = relationship("Team", back_populates="members")
    # Note: user relationship is defined in User model to avoid circular imports

    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id})>"

    @classmethod
    def is_member(cls, session, team_id: str, user_id: str) -> bool:
        """Check if a user is a member of a team."""
        return session.query(cls).filter_by(team_id=team_id, user_id=user_id).first() is not None
