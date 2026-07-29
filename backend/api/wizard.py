"""
Wizard API Router for Q&A functionality.

This router provides endpoints for the wizard utility including:
- Getting Q&A categories
- Retrieving Q&A items with filtering and pagination
- Submitting user feedback
- Getting popular questions
- Searching Q&A content
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, desc, select
from typing import Annotated, List, Optional
from datetime import datetime, timedelta

from backend.core.dependencies import get_db_session
from backend.models.wizard_models import QACategory, QAItem, UserInteraction
from backend.core.security import get_current_user
from backend.models.wizard_schemas import (
    QACategoryResponse,
    UserFeedback,
    QAListResponse,
    QASearchRequest,
    QASearchResponse,
)

router = APIRouter(prefix="/api/wizard", tags=["Wizard Utility"])


@router.get("/categories", response_model=List[QACategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db_session)):
    """
    Get all Q&A categories.

    Returns:
        List of Q&A categories with question counts
    """
    result = await db.execute(select(QACategory))
    categories = result.scalars().all()

    # Add question counts to each category
    for category in categories:
        count_result = await db.execute(select(func.count()).where(QAItem.category_id == category.id, QAItem.is_active))
        category.question_count = count_result.scalar()

    return categories


@router.get("/qa", response_model=QAListResponse)
async def get_qa_items(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get Q&A items with optional filtering and pagination.

    Args:
        category_id: Filter by category ID
        search: Search term to filter questions/answers
        limit: Number of items to return (default: 20)
        offset: Pagination offset (default: 0)

    Returns:
        Paginated list of Q&A items with metadata
    """
    # Build the base query
    stmt = select(QAItem).where(QAItem.is_active).options(joinedload(QAItem.category))

    if category_id:
        stmt = stmt.where(QAItem.category_id == category_id)

    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(or_(QAItem.question.ilike(search_term), QAItem.answer.ilike(search_term)))

    # Get total count
    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar()

    # Get paginated items
    items_result = await db.execute(stmt.offset(offset).limit(limit))
    items = items_result.scalars().all()

    # Add view counts and feedback scores to each item
    for item in items:
        view_count_result = await db.execute(
            select(func.count()).where(
                UserInteraction.qa_item_id == item.id, UserInteraction.interaction_type == "view"
            )
        )
        item.view_count = view_count_result.scalar()

        feedback_scores_result = await db.execute(
            select(UserInteraction.feedback_score).where(
                UserInteraction.qa_item_id == item.id,
                UserInteraction.interaction_type == "feedback",
                UserInteraction.feedback_score.isnot(None),
            )
        )
        feedback_scores = feedback_scores_result.scalars().all()

        if feedback_scores:
            item.feedback_score = sum(feedback_scores) / len(feedback_scores)
        else:
            item.feedback_score = 0.0

    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.post("/feedback")
async def submit_feedback(
    feedback: UserFeedback,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    """
    Submit user feedback on a Q&A item.

    Args:
        feedback: User feedback data (qa_item_id, feedback_score, feedback_comment)

    Returns:
        Success message
    """
    # Validate feedback score
    if feedback.feedback_score is not None and (feedback.feedback_score < 1 or feedback.feedback_score > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback score must be between 1 and 5")

    interaction = UserInteraction(
        user_id=current_user["user_id"],
        qa_item_id=feedback.qa_item_id,
        interaction_type="feedback",
        feedback_score=feedback.feedback_score,
        feedback_comment=feedback.feedback_comment,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
    )

    db.add(interaction)
    await db.commit()

    return {"success": True, "message": "Feedback submitted successfully"}


@router.get("/popular")
async def get_popular_questions(
    limit: int = 10, timeframe: Optional[str] = "all", db: AsyncSession = Depends(get_db_session)
):
    """
    Get most popular questions based on view count.

    Args:
        limit: Number of popular items to return (default: 10)
        timeframe: Timeframe for popularity (day, week, month, all)

    Returns:
        List of popular questions with view counts
    """
    # Build the base query
    stmt = (
        select(
            QAItem.id,
            QAItem.question,
            QACategory.name.label("category"),
            func.count(UserInteraction.id).label("view_count"),
        )
        .join(QACategory, QAItem.category_id == QACategory.id)
        .outerjoin(
            UserInteraction,
            (UserInteraction.qa_item_id == QAItem.id) & (UserInteraction.interaction_type == "view"),
        )
        .where(QAItem.is_active)
        .group_by(QAItem.id, QAItem.question, QACategory.name)
        .order_by(desc(func.count(UserInteraction.id)))
        .limit(limit)
    )

    # Apply timeframe filter
    if timeframe != "all":
        now = datetime.now()
        if timeframe == "day":
            start_time = now - timedelta(days=1)
        elif timeframe == "week":
            start_time = now - timedelta(weeks=1)
        elif timeframe == "month":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=365)

        stmt = stmt.where(UserInteraction.created_at >= start_time)

    result = await db.execute(stmt)
    results = result.all()

    return [
        {"id": item.id, "question": item.question, "category": item.category, "view_count": item.view_count}
        for item in results
    ]


@router.post("/search", response_model=QASearchResponse)
async def search_qa(search_request: QASearchRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Search Q&A items by query.

    Args:
        search_request: Search request with query and filters

    Returns:
        Search results with relevance information
    """
    stmt = select(QAItem).where(QAItem.is_active).options(joinedload(QAItem.category))

    if search_request.query:
        search_term = f"%{search_request.query}%"
        stmt = stmt.where(or_(QAItem.question.ilike(search_term), QAItem.answer.ilike(search_term)))

    if search_request.category_ids:
        stmt = stmt.where(QAItem.category_id.in_(search_request.category_ids))

    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar()

    results_result = await db.execute(stmt.limit(search_request.limit or 10))
    results = results_result.scalars().all()

    # Format results with additional information
    formatted_results = []
    for item in results:
        formatted_results.append(
            {
                "id": item.id,
                "question": item.question,
                "answer_preview": item.answer[:200] + "..." if len(item.answer) > 200 else item.answer,
                "category": item.category.name if item.category else "General",
                "relevance_score": 1.0,  # Placeholder for future relevance algorithm
            }
        )

    return {"total": total, "results": formatted_results}
