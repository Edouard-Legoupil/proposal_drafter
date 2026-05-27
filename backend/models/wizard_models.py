"""
SQLAlchemy models for the Wizard Utility Q&A system.

This module defines the database models for the wizard utility,
including Q&A categories, Q&A items, and user interactions.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models import Base


class QACategory(Base):
    """Model for Q&A categories."""
    __tablename__ = 'qa_categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship to QA items
    qa_items = relationship("QAItem", back_populates="category")


class QAItem(Base):
    """Model for individual Q&A items."""
    __tablename__ = 'qa_items'
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False, unique=True)
    answer = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey('qa_categories.id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    category = relationship("QACategory", back_populates="qa_items")
    interactions = relationship("UserInteraction", back_populates="qa_item")


class UserInteraction(Base):
    """Model for tracking user interactions with Q&A items."""
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    qa_item_id = Column(Integer, ForeignKey('qa_items.id'))
    interaction_type = Column(String(50), nullable=False)
    feedback_score = Column(Integer)
    feedback_comment = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    qa_item = relationship("QAItem", back_populates="interactions")
    
    __table_args__ = (
        CheckConstraint("interaction_type IN ('view', 'search', 'feedback')", name="check_interaction_type"),
        CheckConstraint("feedback_score BETWEEN 1 AND 5", name="check_feedback_score")
    )