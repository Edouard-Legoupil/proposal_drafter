"""
Review ORM Models for Proposal Drafter

Defines the review models for the Proposal Drafter system.
"""

from typing import Any, Optional
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Integer
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

# Type alias for mypy - this is the proper way to handle SQLAlchemy declarative base
Base = declarative_base()  # type: ignore[valid-type]


class ProposalPeerReview(Base):  # type: ignore[valid-type, misc]
    """
    ProposalPeerReview model representing peer reviews of proposals.

    Attributes:
        id: Unique UUID identifier
        proposal_id: Foreign key to the proposal being reviewed
        reviewer_id: User who conducted the review
        comments: Review comments
        status: Review status
        rating: Review rating
        created_at: Timestamp when review was created
        updated_at: Timestamp when review was last updated
    """

    __tablename__ = "proposal_peer_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), nullable=False)
    comments = Column(Text, nullable=True)
    status = Column(String, default="pending")
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    proposal = relationship("Proposal", backref="peer_reviews")

    def __repr__(self):
        return f"<ProposalPeerReview(id={self.id}, proposal_id={self.proposal_id}, status='{self.status}')>"

    @classmethod
    def get_by_id(cls, session, review_id: Any) -> Optional["ProposalPeerReview"]:
        """Get a proposal peer review by its ID."""
        return session.query(cls).filter_by(id=review_id).first()

    @classmethod
    def get_by_proposal(cls, session, proposal_id: str) -> list["ProposalPeerReview"]:
        """Get all peer reviews for a proposal."""
        return session.query(cls).filter_by(proposal_id=proposal_id).all()


class KnowledgeCardReview(Base):  # type: ignore[valid-type, misc]
    """
    KnowledgeCardReview model representing reviews of knowledge cards.

    Attributes:
        id: Unique UUID identifier
        knowledge_card_id: Foreign key to the knowledge card being reviewed
        reviewer_id: User who conducted the review
        comments: Review comments
        status: Review status
        rating: Review rating
        created_at: Timestamp when review was created
        updated_at: Timestamp when review was last updated
    """

    __tablename__ = "knowledge_card_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    knowledge_card_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_cards.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), nullable=False)
    comments = Column(Text, nullable=True)
    status = Column(String, default="pending")
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    knowledge_card = relationship("KnowledgeCard", backref="reviews")

    def __repr__(self):
        return (
            f"<KnowledgeCardReview(id={self.id}, knowledge_card_id={self.knowledge_card_id}, status='{self.status}')>"
        )

    @classmethod
    def get_by_id(cls, session, review_id: Any) -> Optional["KnowledgeCardReview"]:
        """Get a knowledge card review by its ID."""
        return session.query(cls).filter_by(id=review_id).first()

    @classmethod
    def get_by_knowledge_card(cls, session, knowledge_card_id: str) -> list["KnowledgeCardReview"]:
        """Get all reviews for a knowledge card."""
        return session.query(cls).filter_by(knowledge_card_id=knowledge_card_id).all()


class TemplateComment(Base):  # type: ignore[valid-type, misc]
    """
    TemplateComment model representing comments on donor template requests.

    Attributes:
        id: Unique UUID identifier
        template_request_id: Foreign key to the template request being commented on
        user_id: User who made the comment
        comment: Comment text
        status: Comment status
        created_at: Timestamp when comment was created
        updated_at: Timestamp when comment was last updated
    """

    __tablename__ = "donor_template_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    template_request_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    comment = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<TemplateComment(id={self.id}, template_request_id={self.template_request_id}, status='{self.status}')>"
        )

    @classmethod
    def get_by_id(cls, session, comment_id: Any) -> Optional["TemplateComment"]:
        """Get a template comment by its ID."""
        return session.query(cls).filter_by(id=comment_id).first()

    @classmethod
    def get_by_template_request(cls, session, template_request_id: str) -> list["TemplateComment"]:
        """Get all comments for a template request."""
        return session.query(cls).filter_by(template_request_id=template_request_id).all()
