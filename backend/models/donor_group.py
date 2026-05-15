"""
Donor Group ORM Model for Proposal Drafter

Defines the DonorGroupMember model for donor group-based access control.
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()  # type: ignore[misc]


class DonorGroupMember(Base):  # type: ignore[misc]
    """
    Association table for the many-to-many relationship between Users and Donor Groups.

    Attributes:
        user_id: Foreign key to users table
        donor_group: Name of the donor group (stored as string, not UUID)

    Note: The database schema uses `user_donor_groups` table with `donor_group` as TEXT,
    not a foreign key to a separate donor_groups table. This model reflects that structure.
    """

    __tablename__ = "user_donor_groups"

    user_id = Column(String, primary_key=True, nullable=False)
    donor_group = Column(String, primary_key=True, nullable=False)

    def __repr__(self):
        return f"<DonorGroupMember(user_id={self.user_id}, donor_group='{self.donor_group}')>"

    @classmethod
    def is_member(cls, session, donor_group: str, user_id: str) -> bool:
        """Check if a user is a member of a donor group."""
        return session.query(cls).filter_by(user_id=user_id, donor_group=donor_group).first() is not None

    @classmethod
    def get_user_groups(cls, session, user_id: str) -> list:
        """Get all donor groups a user belongs to."""
        results = session.query(cls).filter_by(user_id=user_id).all()
        return [dg.donor_group for dg in results]
