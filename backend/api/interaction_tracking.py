"""
Interaction Tracking API Endpoints

This module provides endpoints for tracking user interactions, sessions, and wizard usage.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from backend.db.session import get_db

from backend.services.interaction_crud import (
    create_user_session,
    end_user_session,
    log_user_interaction,
    log_wizard_interaction,
    get_user_interactions,
    get_wizard_interactions,
    get_user_journey_patterns,
    get_interaction_analytics,
)


from backend.models.user import User

from backend.models.interaction import (
    UserSessionCreate,
    UserInteractionCreate,
    WizardInteractionCreate,
    UserSessionResponse,
    UserInteractionResponse,
    WizardInteractionResponse,
    UserJourneyPattern,
    InteractionAnalytics,
)
from backend.core.security import get_current_user

router = APIRouter(
    prefix="/interactions",
    tags=["interaction_tracking"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/sessions/",
    response_model=UserSessionResponse,
    summary="Start a new user session",
    description="Creates a new user session for tracking interactions",
)
async def start_user_session(
    session_data: UserSessionCreate, current_user: User = Depends(get_current_user), db=Depends(get_db)
) -> UserSessionResponse:
    """
    Start a new user session.

    Args:
        session_data: Session metadata (device info, browser, etc.)
        current_user: Authenticated user
        db: Database session

    Returns:
        Created session information
    """
    try:
        session = await create_user_session(db, current_user.id, session_data)
        return UserSessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            started_at=session.started_at,
            message="Session started successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start session: {str(e)}"
        )


@router.put(
    "/sessions/{session_id}/end",
    response_model=Dict[str, str],
    summary="End a user session",
    description="Marks a user session as ended",
)
async def end_session(
    session_id: UUID, current_user: User = Depends(get_current_user), db=Depends(get_db)
) -> Dict[str, str]:
    """
    End a user session.

    Args:
        session_id: Session ID to end
        current_user: Authenticated user
        db: Database session

    Returns:
        Confirmation message
    """
    try:
        await end_user_session(db, session_id, current_user.id)
        return {"message": "Session ended successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Session not found or already ended: {str(e)}"
        )


@router.post(
    "/log/",
    response_model=UserInteractionResponse,
    summary="Log a user interaction",
    description="Records a user interaction for analytics and debugging",
)
async def log_interaction(
    interaction_data: UserInteractionCreate, current_user: User = Depends(get_current_user), db=Depends(get_db)
) -> UserInteractionResponse:
    """
    Log a user interaction.

    Args:
        interaction_data: Interaction details
        current_user: Authenticated user
        db: Database session

    Returns:
        Created interaction information
    """
    try:
        interaction = await log_user_interaction(db, interaction_data)
        return UserInteractionResponse(
            interaction_id=interaction.interaction_id,
            session_id=interaction.session_id,
            user_id=interaction.user_id,
            interaction_type=interaction.interaction_type,
            interaction_timestamp=interaction.interaction_timestamp,
            message="Interaction logged successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to log interaction: {str(e)}"
        )


@router.post(
    "/wizard/log/",
    response_model=WizardInteractionResponse,
    summary="Log a wizard interaction",
    description="Records a wizard-specific interaction for learning and improvement",
)
async def log_wizard_interaction(
    wizard_data: WizardInteractionCreate, current_user: User = Depends(get_current_user), db=Depends(get_db)
) -> WizardInteractionResponse:
    """
    Log a wizard interaction.

    Args:
        wizard_data: Wizard interaction details
        current_user: Authenticated user
        db: Database session

    Returns:
        Created wizard interaction information
    """
    try:
        wizard_interaction = await log_wizard_interaction(db, wizard_data)
        return WizardInteractionResponse(
            wizard_interaction_id=wizard_interaction.wizard_interaction_id,
            interaction_id=wizard_interaction.interaction_id,
            session_id=wizard_interaction.session_id,
            user_id=wizard_interaction.user_id,
            action_type=wizard_interaction.action_type,
            interaction_timestamp=wizard_interaction.interaction_timestamp,
            message="Wizard interaction logged successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to log wizard interaction: {str(e)}"
        )


@router.get(
    "/users/{user_id}/interactions/",
    response_model=List[UserInteractionResponse],
    summary="Get user interactions",
    description="Retrieves all interactions for a specific user",
)
async def get_user_interactions_endpoint(
    user_id: UUID,
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    interaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
) -> List[UserInteractionResponse]:
    """
    Get user interactions with filtering options.

    Args:
        user_id: User ID to fetch interactions for
        limit: Maximum number of results
        offset: Pagination offset
        start_date: Filter by start date
        end_date: Filter by end date
        interaction_type: Filter by interaction type
        current_user: Authenticated user (must be admin or same user)
        db: Database session

    Returns:
        List of user interactions
    """
    # Check permissions - only admin or the user themselves can access
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this user's interactions"
        )

    try:
        interactions = await get_user_interactions(db, user_id, limit, offset, start_date, end_date, interaction_type)
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
                error_message=interaction.error_message,
            )
            for interaction in interactions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve interactions: {str(e)}"
        )


@router.get(
    "/users/{user_id}/wizard-interactions/",
    response_model=List[WizardInteractionResponse],
    summary="Get user wizard interactions",
    description="Retrieves all wizard interactions for a specific user",
)
async def get_user_wizard_interactions(
    user_id: UUID, limit: int = 100, offset: int = 0, current_user: User = Depends(get_current_user), db=Depends(get_db)
) -> List[WizardInteractionResponse]:
    """
    Get user wizard interactions.

    Args:
        user_id: User ID to fetch wizard interactions for
        limit: Maximum number of results
        offset: Pagination offset
        current_user: Authenticated user (must be admin or same user)
        db: Database session

    Returns:
        List of wizard interactions
    """
    # Check permissions
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this user's wizard interactions"
        )

    try:
        interactions = await get_wizard_interactions(db, user_id, limit, offset)
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
                was_helpful=interaction.was_helpful,
            )
            for interaction in interactions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve wizard interactions: {str(e)}",
        )


@router.get(
    "/users/{user_id}/journey-patterns/",
    response_model=List[UserJourneyPattern],
    summary="Get user journey patterns",
    description="Retrieves common journey patterns for a user",
)
async def get_journey_patterns(
    user_id: UUID, current_user: User = Depends(get_current_user), db=Depends(get_db)
) -> List[UserJourneyPattern]:
    """
    Get user journey patterns.

    Args:
        user_id: User ID to analyze
        current_user: Authenticated user (must be admin or same user)
        db: Database session

    Returns:
        List of journey patterns
    """
    # Check permissions
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this user's journey patterns"
        )

    try:
        patterns = await get_user_journey_patterns(db, user_id)
        return [
            UserJourneyPattern(
                pattern_id=pattern.pattern_id,
                pattern_name=pattern.pattern_name,
                pattern_description=pattern.pattern_description,
                interaction_sequence=pattern.interaction_sequence,
                frequency_count=pattern.frequency_count,
                last_observed=pattern.last_observed,
                typical_duration=pattern.typical_duration,
                common_next_steps=pattern.common_next_steps,
                related_questions=pattern.related_questions,
            )
            for pattern in patterns
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve journey patterns: {str(e)}"
        )


@router.get(
    "/analytics/",
    response_model=InteractionAnalytics,
    summary="Get interaction analytics",
    description="Retrieves aggregated analytics data for interactions",
)
async def get_analytics(
    date_range: Optional[str] = "30d", current_user: User = Depends(get_current_user), db=Depends(get_db)
) -> InteractionAnalytics:
    """
    Get interaction analytics.

    Args:
        date_range: Time period for analytics (7d, 30d, 90d, all)
        current_user: Authenticated user (admin only)
        db: Database session

    Returns:
        Aggregated analytics data
    """
    # Admin only endpoint
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    try:
        # Parse date range
        end_date = datetime.now()
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:  # all
            start_date = end_date - timedelta(days=365)

        analytics = await get_interaction_analytics(db, start_date, end_date)

        return InteractionAnalytics(
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            total_interactions=analytics.total_interactions,
            total_sessions=analytics.total_sessions,
            total_users=analytics.total_users,
            average_interactions_per_session=analytics.avg_interactions_per_session,
            average_session_duration=analytics.avg_session_duration,
            interaction_types=analytics.interaction_types,
            most_used_features=analytics.most_used_features,
            error_rate=analytics.error_rate,
            wizard_usage_stats=analytics.wizard_usage_stats,
            common_journey_patterns=analytics.common_journey_patterns,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.get(
    "/suggestions/",
    response_model=List[Dict[str, Any]],
    summary="Get context-aware suggestions",
    description="Provides suggestions based on user's interaction history",
)
async def get_context_aware_suggestions(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    current_page: Optional[str] = None,
    current_component: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get context-aware suggestions based on user's interaction history.

    Args:
        current_user: Authenticated user
        db: Database session
        current_page: Current page URL
        current_component: Current component name

    Returns:
        List of suggested actions, questions, or help topics
    """
    try:
        # Get user's recent interactions
        recent_interactions = await get_user_interactions(
            db, current_user.id, limit=50, start_date=datetime.now() - timedelta(hours=2)
        )

        # Get user's journey patterns
        patterns = await get_user_journey_patterns(db, current_user.id)

        # Generate suggestions based on context and history
        suggestions = []

        # 1. Suggest common next steps based on current context
        if current_page:
            common_next_steps = await get_common_next_steps(db, current_user.id, current_page)
            for step in common_next_steps:
                suggestions.append(
                    {
                        "type": "navigation",
                        "title": f"Common next step: {step['description']}",
                        "action": step["action"],
                        "confidence": step["confidence"],
                        "source": "journey_patterns",
                    }
                )

        # 2. Suggest help topics based on recent errors
        recent_errors = [i for i in recent_interactions if not i.was_successful]
        if recent_errors:
            error_topics = await get_help_topics_for_errors(db, recent_errors)
            for topic in error_topics:
                suggestions.append(
                    {
                        "type": "help",
                        "title": f"Help with: {topic['title']}",
                        "content": topic["content"],
                        "related_questions": topic["related_questions"],
                        "source": "error_analysis",
                    }
                )

        # 3. Suggest wizard questions based on current component
        if current_component:
            component_questions = await get_relevant_wizard_questions(db, current_user.id, current_component)
            for question in component_questions:
                suggestions.append(
                    {
                        "type": "wizard",
                        "title": f"Related question: {question['question']}",
                        "question_id": question["question_id"],
                        "category": question["category"],
                        "confidence": question["confidence"],
                        "source": "wizard_learning",
                    }
                )

        # 4. Suggest features the user hasn't tried but others find useful
        unused_features = await get_unused_but_popular_features(db, current_user.id)
        for feature in unused_features:
            suggestions.append(
                {
                    "type": "feature",
                    "title": f"Discover: {feature['name']}",
                    "description": feature["description"],
                    "popularity": feature["popularity"],
                    "source": "feature_discovery",
                }
            )

        # Sort by confidence/importance
        suggestions.sort(key=lambda x: x.get("confidence", 0) or x.get("popularity", 0), reverse=True)

        return suggestions[:10]  # Return top 10 suggestions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate suggestions: {str(e)}"
        )
