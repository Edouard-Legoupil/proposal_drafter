"""
Interaction Tracking Models

This module contains Pydantic models for user interaction tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class InteractionType(str, Enum):
    """Enum for interaction types."""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    FORM_SUBMISSION = "form_submission"
    NAVIGATION = "navigation"
    SEARCH = "search"
    WIZARD_INTERACTION = "wizard_interaction"
    ERROR = "error"
    API_CALL = "api_call"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    COPY_TO_CLIPBOARD = "copy_to_clipboard"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"
    HOVER = "hover"
    SCROLL = "scroll"
    RESIZE = "resize"


class UserSessionCreate(BaseModel):
    """Model for creating a new user session."""
    ip_address: Optional[str] = Field(None, description="User's IP address")
    user_agent: Optional[str] = Field(None, description="User's browser user agent")
    device_type: Optional[str] = Field(None, description="Device type (mobile, desktop, tablet)")
    browser_name: Optional[str] = Field(None, description="Browser name")
    browser_version: Optional[str] = Field(None, description="Browser version")
    os_name: Optional[str] = Field(None, description="Operating system name")
    os_version: Optional[str] = Field(None, description="Operating system version")
    screen_width: Optional[int] = Field(None, description="Screen width in pixels")
    screen_height: Optional[int] = Field(None, description="Screen height in pixels")
    is_mobile: Optional[bool] = Field(None, description="Whether the device is mobile")


class UserSessionResponse(BaseModel):
    """Model for user session response."""
    session_id: UUID
    user_id: UUID
    started_at: datetime
    message: str = "Session started successfully"


class UserInteractionCreate(BaseModel):
    """Model for creating a new user interaction."""
    session_id: UUID = Field(..., description="Session ID")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    page_url: str = Field(..., description="Page URL where interaction occurred")
    page_title: Optional[str] = Field(None, description="Page title")
    component_name: Optional[str] = Field(None, description="Component name")
    element_type: Optional[str] = Field(None, description="Element type (button, input, etc.)")
    element_selector: Optional[str] = Field(None, description="CSS selector for the element")
    element_test_id: Optional[str] = Field(None, description="Test ID of the element")
    element_text: Optional[str] = Field(None, description="Text content of the element")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    duration_ms: Optional[int] = Field(None, description="Duration of the interaction in milliseconds")
    was_successful: Optional[bool] = Field(True, description="Whether the interaction was successful")
    error_message: Optional[str] = Field(None, description="Error message if applicable")
    error_stack: Optional[str] = Field(None, description="Error stack trace if applicable")


class UserInteractionResponse(BaseModel):
    """Model for user interaction response."""
    interaction_id: UUID
    session_id: UUID
    user_id: Optional[UUID] = None
    interaction_type: InteractionType
    interaction_timestamp: datetime
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    component_name: Optional[str] = None
    element_type: Optional[str] = None
    element_test_id: Optional[str] = None
    element_text: Optional[str] = None
    was_successful: Optional[bool] = True
    error_message: Optional[str] = None


class WizardInteractionCreate(BaseModel):
    """Model for creating a new wizard interaction."""
    interaction_id: UUID = Field(..., description="Associated user interaction ID")
    session_id: UUID = Field(..., description="Session ID")
    action_type: str = Field(..., description="Type of wizard action")
    search_query: Optional[str] = Field(None, description="Search query if applicable")
    selected_category_id: Optional[UUID] = Field(None, description="Selected category ID")
    viewed_qa_item_id: Optional[UUID] = Field(None, description="Viewed QA item ID")
    feedback_score: Optional[int] = Field(None, description="Feedback score (1-5)")
    feedback_comment: Optional[str] = Field(None, description="Feedback comment")
    time_spent_ms: Optional[int] = Field(None, description="Time spent on the interaction")
    was_helpful: Optional[bool] = Field(None, description="Whether the interaction was helpful")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data")


class WizardInteractionResponse(BaseModel):
    """Model for wizard interaction response."""
    wizard_interaction_id: UUID
    interaction_id: UUID
    session_id: UUID
    user_id: Optional[UUID] = None
    action_type: str
    interaction_timestamp: datetime
    search_query: Optional[str] = None
    selected_category_id: Optional[UUID] = None
    viewed_qa_item_id: Optional[UUID] = None
    feedback_score: Optional[int] = None
    feedback_comment: Optional[str] = None
    time_spent_ms: Optional[int] = None
    was_helpful: Optional[bool] = None


class UserJourneyPattern(BaseModel):
    """Model for user journey patterns."""
    pattern_id: UUID
    pattern_name: str
    pattern_description: Optional[str] = None
    interaction_sequence: Dict[str, Any] = Field(..., description="Sequence of interactions")
    frequency_count: int = Field(..., description="How often this pattern occurs")
    last_observed: Optional[datetime] = None
    typical_duration: Optional[str] = None  # ISO duration format
    common_next_steps: Dict[str, Any] = Field(..., description="Common next steps after this pattern")
    related_questions: List[Dict[str, Any]] = Field(..., description="Questions related to this pattern")


class InteractionTypeStats(BaseModel):
    """Model for interaction type statistics."""
    type: str
    count: int
    percentage: float


class FeatureUsageStats(BaseModel):
    """Model for feature usage statistics."""
    feature: str
    usage_count: int
    user_count: int
    popularity_score: float


class WizardUsageStats(BaseModel):
    """Model for wizard usage statistics."""
    total_usage: int
    average_feedback_score: float
    helpful_percentage: float
    common_questions: List[Dict[str, Any]]


class JourneyPatternStats(BaseModel):
    """Model for journey pattern statistics."""
    pattern_name: str
    frequency: int
    user_count: int


class InteractionAnalytics(BaseModel):
    """Model for interaction analytics."""
    date_range: str
    start_date: datetime
    end_date: datetime
    total_interactions: int
    total_sessions: int
    total_users: int
    average_interactions_per_session: float
    average_session_duration: Optional[str] = None  # ISO duration format
    interaction_types: List[InteractionTypeStats]
    most_used_features: List[FeatureUsageStats]
    error_rate: float
    wizard_usage_stats: WizardUsageStats
    common_journey_patterns: List[JourneyPatternStats]


class ContextAwareSuggestion(BaseModel):
    """Model for context-aware suggestions."""
    type: str = Field(..., description="Type of suggestion (navigation, help, wizard, feature)")
    title: str = Field(..., description="Suggestion title")
    description: Optional[str] = Field(None, description="Detailed description")
    action: Optional[Dict[str, Any]] = Field(None, description="Action to perform")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    source: str = Field(..., description="Source of the suggestion")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")