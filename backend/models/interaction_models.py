"""
Interaction Tracking Database Models

This module contains SQLAlchemy models for user interaction tracking.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Interval
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


# Define interaction_type enum
class InteractionTypeENUM(ENUM):
    """Enum for interaction types."""

    def __init__(self):
        super().__init__(name="interaction_type", create_type=False)


class UserSession(Base):
    """User session tracking model."""

    __tablename__ = "user_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)
    browser_name = Column(String(50), nullable=True)
    browser_version = Column(String(20), nullable=True)
    os_name = Column(String(50), nullable=True)
    os_version = Column(String(20), nullable=True)
    screen_width = Column(Integer, nullable=True)
    screen_height = Column(Integer, nullable=True)
    is_mobile = Column(Boolean, nullable=True)
    session_duration = Column(Interval, server_default=text("(ended_at - started_at)"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    interactions = relationship("UserInteraction", back_populates="session", cascade="all, delete-orphan")
    wizard_interactions = relationship("WizardInteraction", back_populates="session", cascade="all, delete-orphan")


class UserInteraction(Base):
    """User interaction tracking model."""

    __tablename__ = "user_interactions"

    interaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.session_id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    interaction_type = Column(InteractionTypeENUM, nullable=False)
    interaction_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    page_url = Column(Text, nullable=False)
    page_title = Column(Text, nullable=True)
    component_name = Column(String(100), nullable=True)
    element_type = Column(String(50), nullable=True)
    element_selector = Column(Text, nullable=True)
    element_test_id = Column(String(100), nullable=True)
    element_text = Column(Text, nullable=True)
    event_data = Column(JSONB, nullable=True)
    metadata = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    was_successful = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    error_stack = Column(Text, nullable=True)

    # Relationships
    session = relationship("UserSession", back_populates="interactions")
    user = relationship("User")
    wizard_interaction = relationship(
        "WizardInteraction", back_populates="interaction", uselist=False, cascade="all, delete-orphan"
    )


class WizardInteraction(Base):
    """Wizard-specific interaction tracking model."""

    __tablename__ = "wizard_interactions"

    wizard_interaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interaction_id = Column(
        UUID(as_uuid=True), ForeignKey("user_interactions.interaction_id", ondelete="CASCADE"), unique=True
    )
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.session_id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    interaction_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    action_type = Column(String(50), nullable=False)
    search_query = Column(Text, nullable=True)
    selected_category_id = Column(
        UUID(as_uuid=True), ForeignKey("wizard_categories.category_id", ondelete="SET NULL"), nullable=True
    )
    viewed_qa_item_id = Column(
        UUID(as_uuid=True), ForeignKey("wizard_qa_items.qa_item_id", ondelete="SET NULL"), nullable=True
    )
    feedback_score = Column(Integer, nullable=True)
    feedback_comment = Column(Text, nullable=True)
    time_spent_ms = Column(Integer, nullable=True)
    was_helpful = Column(Boolean, nullable=True)
    related_qa_items = Column(JSONB, nullable=True)
    context_data = Column(JSONB, nullable=True)

    # Relationships
    interaction = relationship("UserInteraction", back_populates="wizard_interaction")
    session = relationship("UserSession", back_populates="wizard_interactions")
    user = relationship("User")
    category = relationship("WizardCategory")
    qa_item = relationship("WizardQAItem")


class UserJourneyPattern(Base):
    """User journey pattern model for analytics."""

    __tablename__ = "user_journey_patterns"

    pattern_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_name = Column(String(100), nullable=False)
    pattern_description = Column(Text, nullable=True)
    interaction_sequence = Column(JSONB, nullable=False)
    frequency_count = Column(Integer, default=0)
    last_observed = Column(DateTime(timezone=True), nullable=True)
    first_observed = Column(DateTime(timezone=True), server_default=func.now())
    typical_duration = Column(Interval, nullable=True)
    common_next_steps = Column(JSONB, nullable=True)
    related_questions = Column(JSONB, nullable=True)


class InteractionAnalytics(Base):
    """Pre-aggregated interaction analytics model."""

    __tablename__ = "interaction_analytics"

    analytics_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    total_interactions = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    total_session_duration = Column(Interval, nullable=True)
    average_session_duration = Column(Interval, nullable=True)
    interaction_types = Column(JSONB, nullable=True)
    most_used_features = Column(JSONB, nullable=True)
    error_count = Column(Integer, default=0)
    wizard_usage_count = Column(Integer, default=0)
    wizard_feedback_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_interaction_analytics_date", "date"),
        Index("idx_interaction_analytics_user_id", "user_id"),
    )
