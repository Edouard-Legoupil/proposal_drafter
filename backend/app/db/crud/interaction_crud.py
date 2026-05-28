"""
Interaction Tracking CRUD Operations

This module contains database operations for user interaction tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, distinct, cast, Integer
from sqlalchemy.sql import text
from sqlalchemy.dialects.postgresql import JSONB, INTERVAL

from app.models.interaction import (
    UserSessionCreate,
    UserInteractionCreate,
    WizardInteractionCreate,
    UserSessionResponse,
    UserInteractionResponse,
    WizardInteractionResponse,
    UserJourneyPattern,
    InteractionAnalytics
)
from app.db.models import (
    UserSession,
    UserInteraction,
    WizardInteraction,
    UserJourneyPattern as DBUserJourneyPattern,
    InteractionAnalytics as DBInteractionAnalytics
)


async def create_user_session(
    db: AsyncSession,
    user_id: UUID,
    session_data: UserSessionCreate
) -> UserSessionResponse:
    """
    Create a new user session.
    
    Args:
        db: Database session
        user_id: User ID
        session_data: Session creation data
        
    Returns:
        Created session response
    """
    session = UserSession(
        user_id=user_id,
        ip_address=session_data.ip_address,
        user_agent=session_data.user_agent,
        device_type=session_data.device_type,
        browser_name=session_data.browser_name,
        browser_version=session_data.browser_version,
        os_name=session_data.os_name,
        os_version=session_data.os_version,
        screen_width=session_data.screen_width,
        screen_height=session_data.screen_height,
        is_mobile=session_data.is_mobile
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return UserSessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        started_at=session.started_at,
        message="Session started successfully"
    )


async def end_user_session(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID
) -> None:
    """
    End a user session.
    
    Args:
        db: Database session
        session_id: Session ID to end
        user_id: User ID (for verification)
        
    Raises:
        Exception: If session not found or already ended
    """
    result = await db.execute(
        select(UserSession)
        .where(
            and_(
                UserSession.session_id == session_id,
                UserSession.user_id == user_id,
                UserSession.ended_at.is_(None)
            )
        )
    )
    
    session = result.scalars().first()
    if not session:
        raise Exception("Session not found or already ended")
    
    session.ended_at = datetime.utcnow()
    await db.commit()


async def log_user_interaction(
    db: AsyncSession,
    interaction_data: UserInteractionCreate
) -> UserInteractionResponse:
    """
    Log a user interaction.
    
    Args:
        db: Database session
        interaction_data: Interaction data
        
    Returns:
        Created interaction response
    """
    interaction = UserInteraction(
        session_id=interaction_data.session_id,
        user_id=interaction_data.user_id,
        interaction_type=interaction_data.interaction_type,
        page_url=interaction_data.page_url,
        page_title=interaction_data.page_title,
        component_name=interaction_data.component_name,
        element_type=interaction_data.element_type,
        element_selector=interaction_data.element_selector,
        element_test_id=interaction_data.element_test_id,
        element_text=interaction_data.element_text,
        event_data=interaction_data.event_data,
        metadata=interaction_data.metadata,
        duration_ms=interaction_data.duration_ms,
        was_successful=interaction_data.was_successful,
        error_message=interaction_data.error_message,
        error_stack=interaction_data.error_stack
    )
    
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    
    return UserInteractionResponse(
        interaction_id=interaction.interaction_id,
        session_id=interaction.session_id,
        user_id=interaction.user_id,
        interaction_type=interaction.interaction_type,
        interaction_timestamp=interaction.interaction_timestamp,
        page_url=interaction.page_url,
        page_title=interaction.page_title,
        component_name=interaction.component_name,
        element_type=interaction.element_type,
        element_test_id=interaction.element_test_id,
        element_text=interaction.element_text,
        was_successful=interaction.was_successful,
        error_message=interaction.error_message
    )


async def log_wizard_interaction(
    db: AsyncSession,
    wizard_data: WizardInteractionCreate
) -> WizardInteractionResponse:
    """
    Log a wizard interaction.
    
    Args:
        db: Database session
        wizard_data: Wizard interaction data
        
    Returns:
        Created wizard interaction response
    """
    wizard_interaction = WizardInteraction(
        interaction_id=wizard_data.interaction_id,
        session_id=wizard_data.session_id,
        user_id=wizard_data.user_id,
        action_type=wizard_data.action_type,
        search_query=wizard_data.search_query,
        selected_category_id=wizard_data.selected_category_id,
        viewed_qa_item_id=wizard_data.viewed_qa_item_id,
        feedback_score=wizard_data.feedback_score,
        feedback_comment=wizard_data.feedback_comment,
        time_spent_ms=wizard_data.time_spent_ms,
        was_helpful=wizard_data.was_helpful,
        context_data=wizard_data.context_data
    )
    
    db.add(wizard_interaction)
    await db.commit()
    await db.refresh(wizard_interaction)
    
    return WizardInteractionResponse(
        wizard_interaction_id=wizard_interaction.wizard_interaction_id,
        interaction_id=wizard_interaction.interaction_id,
        session_id=wizard_interaction.session_id,
        user_id=wizard_interaction.user_id,
        action_type=wizard_interaction.action_type,
        interaction_timestamp=wizard_interaction.interaction_timestamp,
        search_query=wizard_interaction.search_query,
        selected_category_id=wizard_interaction.selected_category_id,
        viewed_qa_item_id=wizard_interaction.viewed_qa_item_id,
        feedback_score=wizard_interaction.feedback_score,
        feedback_comment=wizard_interaction.feedback_comment,
        time_spent_ms=wizard_interaction.time_spent_ms,
        was_helpful=wizard_interaction.was_helpful
    )


async def get_user_interactions(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    interaction_type: Optional[str] = None
) -> List[UserInteractionResponse]:
    """
    Get user interactions with filtering.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum results
        offset: Pagination offset
        start_date: Filter by start date
        end_date: Filter by end date
        interaction_type: Filter by interaction type
        
    Returns:
        List of user interactions
    """
    query = select(UserInteraction).where(UserInteraction.user_id == user_id)
    
    # Apply filters
    if start_date:
        query = query.where(UserInteraction.interaction_timestamp >= start_date)
    if end_date:
        query = query.where(UserInteraction.interaction_timestamp <= end_date)
    if interaction_type:
        query = query.where(UserInteraction.interaction_type == interaction_type)
    
    query = query.order_by(desc(UserInteraction.interaction_timestamp))
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    return [
        UserInteractionResponse(
            interaction_id=interaction.interaction_id,
            session_id=interaction.session_id,
            user_id=interaction.user_id,
            interaction_type=interaction.interaction_type,
            interaction_timestamp=interaction.interaction_timestamp,
            page_url=interaction.page_url,
            page_title=interaction.page_title,
            component_name=interaction.component_name,
            element_type=interaction.element_type,
            element_test_id=interaction.element_test_id,
            element_text=interaction.element_text,
            was_successful=interaction.was_successful,
            error_message=interaction.error_message
        ) for interaction in interactions
    ]


async def get_wizard_interactions(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 100,
    offset: int = 0
) -> List[WizardInteractionResponse]:
    """
    Get wizard interactions for a user.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum results
        offset: Pagination offset
        
    Returns:
        List of wizard interactions
    """
    query = (
        select(WizardInteraction)
        .where(WizardInteraction.user_id == user_id)
        .order_by(desc(WizardInteraction.interaction_timestamp))
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    return [
        WizardInteractionResponse(
            wizard_interaction_id=interaction.wizard_interaction_id,
            interaction_id=interaction.interaction_id,
            session_id=interaction.session_id,
            user_id=interaction.user_id,
            action_type=interaction.action_type,
            interaction_timestamp=interaction.interaction_timestamp,
            search_query=interaction.search_query,
            selected_category_id=interaction.selected_category_id,
            viewed_qa_item_id=interaction.viewed_qa_item_id,
            feedback_score=interaction.feedback_score,
            feedback_comment=interaction.feedback_comment,
            time_spent_ms=interaction.time_spent_ms,
            was_helpful=interaction.was_helpful
        ) for interaction in interactions
    ]


async def get_user_journey_patterns(
    db: AsyncSession,
    user_id: UUID
) -> List[UserJourneyPattern]:
    """
    Get user journey patterns.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List of journey patterns
    """
    # This would be implemented with more sophisticated pattern recognition
    # For now, return a basic implementation
    
    query = (
        select(DBUserJourneyPattern)
        .order_by(desc(DBUserJourneyPattern.frequency_count))
        .limit(10)
    )
    
    result = await db.execute(query)
    patterns = result.scalars().all()
    
    return [
        UserJourneyPattern(
            pattern_id=pattern.pattern_id,
            pattern_name=pattern.pattern_name,
            pattern_description=pattern.pattern_description,
            interaction_sequence=pattern.interaction_sequence,
            frequency_count=pattern.frequency_count,
            last_observed=pattern.last_observed,
            typical_duration=str(pattern.typical_duration) if pattern.typical_duration else None,
            common_next_steps=pattern.common_next_steps,
            related_questions=pattern.related_questions
        ) for pattern in patterns
    ]


async def get_interaction_analytics(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> InteractionAnalytics:
    """
    Get interaction analytics for a date range.
    
    Args:
        db: Database session
        start_date: Start date
        end_date: End date
        
    Returns:
        Interaction analytics data
    """
    # Calculate basic statistics
    total_interactions_result = await db.execute(
        select([func.count()])
        .select_from(UserInteraction)
        .where(
            and_(
                UserInteraction.interaction_timestamp >= start_date,
                UserInteraction.interaction_timestamp <= end_date
            )
        )
    )
    total_interactions = total_interactions_result.scalar() or 0
    
    total_sessions_result = await db.execute(
        select([func.count(distinct(UserInteraction.session_id))])
        .select_from(UserInteraction)
        .where(
            and_(
                UserInteraction.interaction_timestamp >= start_date,
                UserInteraction.interaction_timestamp <= end_date
            )
        )
    )
    total_sessions = total_sessions_result.scalar() or 0
    
    total_users_result = await db.execute(
        select([func.count(distinct(UserInteraction.user_id))])
        .select_from(UserInteraction)
        .where(
            and_(
                UserInteraction.interaction_timestamp >= start_date,
                UserInteraction.interaction_timestamp <= end_date
            )
        )
    )
    total_users = total_users_result.scalar() or 0
    
    # Calculate interaction types distribution
    interaction_types_result = await db.execute(
        select([
            UserInteraction.interaction_type,
            func.count().label('count')
        ])
        .select_from(UserInteraction)
        .where(
            and_(
                UserInteraction.interaction_timestamp >= start_date,
                UserInteraction.interaction_timestamp <= end_date
            )
        )
        .group_by(UserInteraction.interaction_type)
        .order_by(desc('count'))
    )
    
    interaction_types_data = []
    total_interactions_for_percent = max(total_interactions, 1)  # Avoid division by zero
    
    for row in interaction_types_result:
        interaction_types_data.append({
            'type': row.interaction_type,
            'count': row.count,
            'percentage': (row.count / total_interactions_for_percent) * 100
        })
    
    # Calculate error rate
    error_count_result = await db.execute(
        select([func.count()])
        .select_from(UserInteraction)
        .where(
            and_(
                UserInteraction.interaction_timestamp >= start_date,
                UserInteraction.interaction_timestamp <= end_date,
                UserInteraction.was_successful.is_(False)
            )
        )
    )
    error_count = error_count_result.scalar() or 0
    error_rate = (error_count / total_interactions_for_percent) * 100 if total_interactions > 0 else 0
    
    # Calculate wizard usage statistics
    wizard_count_result = await db.execute(
        select([func.count()])
        .select_from(WizardInteraction)
        .where(
            and_(
                WizardInteraction.interaction_timestamp >= start_date,
                WizardInteraction.interaction_timestamp <= end_date
            )
        )
    )
    wizard_count = wizard_count_result.scalar() or 0
    
    # Calculate average feedback score
    feedback_result = await db.execute(
        select([func.avg(WizardInteraction.feedback_score)])
        .select_from(WizardInteraction)
        .where(
            and_(
                WizardInteraction.interaction_timestamp >= start_date,
                WizardInteraction.interaction_timestamp <= end_date,
                WizardInteraction.feedback_score.isnot(None)
            )
        )
    )
    avg_feedback_score = feedback_result.scalar() or 0
    
    # Calculate helpful percentage
    helpful_result = await db.execute(
        select([func.count()])
        .select_from(WizardInteraction)
        .where(
            and_(
                WizardInteraction.interaction_timestamp >= start_date,
                WizardInteraction.interaction_timestamp <= end_date,
                WizardInteraction.was_helpful.is_(True)
            )
        )
    )
    helpful_count = helpful_result.scalar() or 0
    helpful_percentage = (helpful_count / max(wizard_count, 1)) * 100 if wizard_count > 0 else 0
    
    return InteractionAnalytics(
        date_range=f"{start_date.date()} to {end_date.date()}",
        start_date=start_date,
        end_date=end_date,
        total_interactions=total_interactions,
        total_sessions=total_sessions,
        total_users=total_users,
        average_interactions_per_session=total_interactions / max(total_sessions, 1),
        average_session_duration=None,  # Would require session duration calculation
        interaction_types=interaction_types_data,
        most_used_features=[],  # Would require feature usage analysis
        error_rate=error_rate,
        wizard_usage_stats={
            'total_usage': wizard_count,
            'average_feedback_score': float(avg_feedback_score),
            'helpful_percentage': float(helpful_percentage),
            'common_questions': []  # Would require question frequency analysis
        },
        common_journey_patterns=[]  # Would require pattern analysis
    )


async def get_common_next_steps(
    db: AsyncSession,
    user_id: UUID,
    current_page: str
) -> List[Dict[str, Any]]:
    """
    Get common next steps based on current page and user history.
    
    Args:
        db: Database session
        user_id: User ID
        current_page: Current page URL
        
    Returns:
        List of common next steps
    """
    # This would be implemented with pattern recognition
    # For now, return a mock implementation
    return [
        {
            'description': 'Navigate to dashboard',
            'action': {'type': 'navigation', 'url': '/dashboard'},
            'confidence': 0.85
        },
        {
            'description': 'Start new proposal',
            'action': {'type': 'navigation', 'url': '/chat'},
            'confidence': 0.72
        }
    ]


async def get_help_topics_for_errors(
    db: AsyncSession,
    recent_errors: List[UserInteractionResponse]
) -> List[Dict[str, Any]]:
    """
    Get help topics based on recent errors.
    
    Args:
        db: Database session
        recent_errors: List of recent error interactions
        
    Returns:
        List of help topics
    """
    # This would be implemented with error pattern matching
    # For now, return a mock implementation
    return [
        {
            'title': 'Form Validation Issues',
            'content': 'Check all required fields and ensure data formats are correct.',
            'related_questions': [
                'How do I fix form validation errors?',
                'What are the required fields for this form?'
            ]
        }
    ]


async def get_relevant_wizard_questions(
    db: AsyncSession,
    user_id: UUID,
    current_component: str
) -> List[Dict[str, Any]]:
    """
    Get relevant wizard questions based on current component and user history.
    
    Args:
        db: Database session
        user_id: User ID
        current_component: Current component name
        
    Returns:
        List of relevant questions
    """
    # This would be implemented with machine learning based on user history
    # For now, return a mock implementation based on component
    component_questions = {
        'proposal_container': [
            {
                'question_id': 'q1',
                'question': 'How do I edit a proposal section?',
                'category': 'Proposal Editing',
                'confidence': 0.92
            },
            {
                'question_id': 'q2',
                'question': 'What are the required sections for a proposal?',
                'category': 'Proposal Structure',
                'confidence': 0.88
            }
        ],
        'knowledge_card': [
            {
                'question_id': 'q3',
                'question': 'How do I create a knowledge card?',
                'category': 'Knowledge Management',
                'confidence': 0.95
            }
        ]
    }
    
    return component_questions.get(current_component, [])


async def get_unused_but_popular_features(
    db: AsyncSession,
    user_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get features that the user hasn't used but are popular among other users.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List of unused but popular features
    """
    # This would be implemented with feature usage analysis
    # For now, return a mock implementation
    return [
        {
            'name': 'Advanced Search',
            'description': 'Use advanced search filters to find knowledge cards more efficiently',
            'popularity': 0.87
        },
        {
            'name': 'Template Gallery',
            'description': 'Browse and use pre-built proposal templates',
            'popularity': 0.91
        }
    ]