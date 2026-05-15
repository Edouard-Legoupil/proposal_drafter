"""
User ORM Model for Proposal Drafter

Defines the User model with authorization methods for object-level access control.
This model integrates with the existing authentication system and provides
methods to check permissions, ownership, team membership, and donor group membership.
"""

import logging
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, func
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy import text

# Local imports for type hints (avoid circular imports)
if TYPE_CHECKING:
    pass

# Use the same base - will be properly configured at runtime
Base = declarative_base()  # type: ignore[misc]

# Configure logger for authorization
logger = logging.getLogger("security.authorization")


class User(Base):  # type: ignore[misc]
    """
    User model representing a user in the Proposal Drafter system.

    This model provides the core authorization methods required for
    object-level access control (T013-T016).

    Attributes:
        id: Unique UUID identifier for the user
        email: User's email address (unique)
        name: User's display name
        password: Hashed password
        team_id: Foreign key to the user's primary team
        is_admin: Whether the user has system admin privileges
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated

    Authorization Methods (T013-T016):
        has_permission(permission): Check if user has a specific permission
        owns_resource(resource_type, resource_id): Check if user owns a resource
        is_team_member(team_id): Check if user is a member of a team
        is_donor_group_member(
            donor_group_id
        ): Check if user is a member of a donor group
    """

    __tablename__ = "users"

    # Columns matching the database schema
    id = Column(String, primary_key=True, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    team_id = Column(String, nullable=True)
    security_questions = Column(Text, nullable=True)
    session_active = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    geographic_coverage_type = Column(String, nullable=True)
    geographic_coverage_region = Column(String, nullable=True)
    geographic_coverage_country = Column(String, nullable=True)
    requested_role_id = Column(Integer, nullable=True)

    # Relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

    # Convenience property to check if user is admin
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges based on roles."""
        return "system admin" in [ur.role.name for ur in self.user_roles if ur.role]

    @property
    def roles(self) -> List[str]:
        """Get list of role names for the user."""
        return [ur.role.name for ur in self.user_roles if ur.role]

    # =========================================================================
    # Authorization Methods (T013-T016)
    # =========================================================================

    def has_permission(self, permission: str, session: Optional[Session] = None) -> bool:
        """
        Check if the user has a specific permission.

        This method checks the user's roles against the required permission.
        Admin users automatically have all permissions.

        Args:
            permission: The permission to check (e.g., 'read', 'write', 'delete',
                       'admin')
            session: Optional SQLAlchemy session for database queries

        Returns:
            True if user has the permission, False otherwise

        Note:
            This is a simplified implementation that checks role names directly.
            For more complex RBAC, you would query a permissions table.
            The current implementation checks if the permission string is in the
            user's role names or if the user has the 'system admin' role.
        """
        # Admin users have all permissions
        if self.is_admin:
            return True

        # Check if the permission matches any of the user's role names
        # This is a simplified approach - in a full RBAC system, you'd have
        # a separate permissions table and role-permission mappings
        return permission in self.roles

    def owns_resource(self, resource_type: str, resource_id: str, session: Optional[Session] = None) -> bool:
        """
        Check if the user owns a specific resource.

        This method queries the database to verify that the user's ID matches
        the owner_id of the specified resource.

        Args:
            resource_type: Type of resource ('proposal', 'knowledge_card', 'template')
            resource_id: ID of the resource to check
            session: Optional SQLAlchemy session for database queries

        Returns:
            True if user owns the resource, False otherwise

        Raises:
            ValueError: If resource_type is unknown
        """
        # Admin users own all resources
        if self.is_admin:
            return True

        # Map resource types to table names
        table_map = {
            "proposal": "proposals",
            "knowledge_card": "knowledge_cards",
            "template": "templates",
        }

        table_name = table_map.get(resource_type)
        if table_name is None:
            raise ValueError(f"Unknown resource type: {resource_type}")

        # Use the provided session or get a new connection
        if session:
            try:
                result = session.execute(
                    text(f"SELECT owner_id FROM {table_name} WHERE id = :id"),
                    {"id": resource_id},
                )
                row = result.fetchone()
                if row and row[0]:
                    return str(row[0]) == str(self.id)
                return False
            except Exception as e:
                logger.error(f"Error checking ownership for {resource_type} {resource_id}: {e}")
                return False
        else:
            # Fallback: use direct database connection
            from backend.core.db import get_engine

            try:
                with get_engine().connect() as connection:
                    result = connection.execute(
                        text(f"SELECT owner_id FROM {table_name} WHERE id = :id"),
                        {"id": resource_id},
                    )
                    row = result.fetchone()
                    if row and row[0]:
                        return str(row[0]) == str(self.id)
                    return False
            except Exception as e:
                logger.error(f"Error checking ownership for {resource_type} {resource_id}: {e}")
                return False

    def is_team_member(self, team_id: str, session: Optional[Session] = None) -> bool:
        """
        Check if the user is a member of a specific team.

        This method queries the team_members table to verify membership.
        Admin users are automatically considered members of all teams.

        Args:
            team_id: ID of the team to check
            session: Optional SQLAlchemy session for database queries

        Returns:
            True if user is a team member, False otherwise
        """
        # Admin users are members of all teams
        if self.is_admin:
            return True

        # Use the provided session or get a new connection
        if session:
            try:
                result = session.execute(
                    text("SELECT 1 FROM team_members " "WHERE team_id = :team_id AND user_id = :user_id"),
                    {"team_id": team_id, "user_id": str(self.id)},
                )
                return result.fetchone() is not None
            except Exception as e:
                logger.error(f"Error checking team membership for team {team_id}: {e}")
                return False
        else:
            # Fallback: use direct database connection
            from backend.core.db import get_engine

            try:
                with get_engine().connect() as connection:
                    result = connection.execute(
                        text("SELECT 1 FROM team_members " "WHERE team_id = :team_id AND user_id = :user_id"),
                        {"team_id": team_id, "user_id": str(self.id)},
                    )
                    return result.fetchone() is not None
            except Exception as e:
                logger.error(f"Error checking team membership for team {team_id}: {e}")
                return False

    def is_donor_group_member(self, donor_group_id: str, session: Optional[Session] = None) -> bool:
        """
        Check if the user is a member of a specific donor group.

        This method queries the donor_group_members table to verify membership.
        Admin users are automatically considered members of all donor groups.

        Args:
            donor_group_id: ID of the donor group to check
            session: Optional SQLAlchemy session for database queries

        Returns:
            True if user is a donor group member, False otherwise
        """
        # Admin users are members of all donor groups
        if self.is_admin:
            return True

        # Use the provided session or get a new connection
        if session:
            try:
                result = session.execute(
                    text(
                        "SELECT 1 FROM donor_group_members "
                        "WHERE donor_group_id = :donor_group_id AND user_id = :user_id"
                    ),
                    {"donor_group_id": donor_group_id, "user_id": str(self.id)},
                )
                return result.fetchone() is not None
            except Exception as e:
                logger.error(f"Error checking donor group membership for group " f"{donor_group_id}: {e}")
                return False
        else:
            # Fallback: use direct database connection
            from backend.core.db import get_engine

            try:
                with get_engine().connect() as connection:
                    result = connection.execute(
                        text(
                            "SELECT 1 FROM donor_group_members "
                            "WHERE donor_group_id = :donor_group_id "
                            "AND user_id = :user_id"
                        ),
                        {"donor_group_id": donor_group_id, "user_id": str(self.id)},
                    )
                    return result.fetchone() is not None
            except Exception as e:
                logger.error(f"Error checking donor group membership for group " f"{donor_group_id}: {e}")
                return False

    # =========================================================================
    # Additional Helper Methods
    # =========================================================================

    def get_owned_resources(self, resource_type: str, session: Optional[Session] = None) -> List[dict]:
        """
        Get all resources owned by this user.

        Args:
            resource_type: Type of resource ('proposal', 'knowledge_card', 'template')
            session: Optional SQLAlchemy session

        Returns:
            List of resource dictionaries
        """
        table_map = {
            "proposal": "proposals",
            "knowledge_card": "knowledge_cards",
            "template": "templates",
        }

        table_name = table_map.get(resource_type)
        if table_name is None:
            raise ValueError(f"Unknown resource type: {resource_type}")

        if session:
            try:
                result = session.execute(
                    text(f"SELECT * FROM {table_name} WHERE owner_id = :owner_id"),
                    {"owner_id": str(self.id)},
                )
                return [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                logger.error(f"Error fetching owned {resource_type}s: {e}")
                return []
        else:
            from backend.core.db import get_engine

            try:
                with get_engine().connect() as connection:
                    result = connection.execute(
                        text(f"SELECT * FROM {table_name} WHERE owner_id = :owner_id"),
                        {"owner_id": str(self.id)},
                    )
                    return [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                logger.error(f"Error fetching owned {resource_type}s: {e}")
                return []

    def get_team_ids(self, session: Optional[Session] = None) -> List[str]:
        """
        Get all team IDs the user is a member of.

        Args:
            session: Optional SQLAlchemy session

        Returns:
            List of team IDs
        """
        if session:
            try:
                result = session.execute(
                    text("SELECT team_id FROM team_members WHERE user_id = :user_id"),
                    {"user_id": str(self.id)},
                )
                return [str(row[0]) for row in result.fetchall()]
            except Exception as e:
                logger.error(f"Error fetching team IDs: {e}")
                return []
        else:
            from backend.core.db import get_engine

            try:
                with get_engine().connect() as connection:
                    result = connection.execute(
                        text("SELECT team_id FROM team_members WHERE user_id = :user_id"),
                        {"user_id": str(self.id)},
                    )
                    return [str(row[0]) for row in result.fetchall()]
            except Exception as e:
                logger.error(f"Error fetching team IDs: {e}")
                return []

    def get_donor_group_ids(self, session: Optional[Session] = None) -> List[str]:
        """
        Get all donor group IDs the user is a member of.

        Args:
            session: Optional SQLAlchemy session

        Returns:
            List of donor group IDs
        """
        if session:
            try:
                result = session.execute(
                    text("SELECT donor_group_id FROM donor_group_members " "WHERE user_id = :user_id"),
                    {"user_id": str(self.id)},
                )
                return [str(row[0]) for row in result.fetchall()]
            except Exception as e:
                logger.error(f"Error fetching donor group IDs: {e}")
                return []
        else:
            from backend.core.db import get_engine

            try:
                with get_engine().connect() as connection:
                    result = connection.execute(
                        text("SELECT donor_group_id FROM donor_group_members " "WHERE user_id = :user_id"),
                        {"user_id": str(self.id)},
                    )
                    return [str(row[0]) for row in result.fetchall()]
            except Exception as e:
                logger.error(f"Error fetching donor group IDs: {e}")
                return []

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', " f"name='{self.name}', is_admin={self.is_admin})>"
