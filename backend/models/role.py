"""
Role ORM Model for Proposal Drafter

Defines the Role and UserRole models for role-based access control.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, relationship

# Use the same base as other models
# This will be set in each model file to avoid circular imports
Base = declarative_base()  # type: ignore[misc]


class Role(Base):
    """
    Role model representing user roles in the system.

    Attributes:
        id: Unique identifier for the role
        name: Name of the role (e.g., 'system admin', 'knowledge manager donors')
        users: Relationship to users who have this role
    """

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)

    # Relationship to UserRole (many-to-many)
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

    @classmethod
    def get_by_name(cls, session, name: str):
        """Get a role by its name."""
        return session.query(cls).filter_by(name=name).first()


class UserRole(Base):
    """
    Association table for the many-to-many relationship between Users and Roles.

    Attributes:
        user_id: Foreign key to users table
        role_id: Foreign key to roles table
        user: Relationship to User
        role: Relationship to Role
    """

    __tablename__ = "user_roles"

    user_id = Column(String, primary_key=True, nullable=False)
    role_id = Column(Integer, primary_key=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
