"""
Wizard API Router for Q&A functionality.

This router provides endpoints for the wizard utility including:
- Getting Q&A categories
- Retrieving Q&A items with filtering and pagination
- Submitting user feedback
- Getting popular questions
- Searching Q&A content
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc
from typing import List, Optional
from datetime import datetime, timedelta

from backend.core.db import get_db
from backend.models.wizard_models import QACategory, QAItem, UserInteraction
from backend.core.security import get_current_user
from backend.schemas.wizard_schemas import (
    QACategoryResponse, 
    QAItemResponse, 
    UserFeedback, 
    QASearchRequest, 
    QASearchResponse
)

router = APIRouter(prefix="/api/wizard", tags=["Wizard Utility"])


@router.get("/categories", response_model=List[QACategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    Get all Q&A categories.
    
    Returns:
        List of Q&A categories with question counts
    """
    categories = db.query(QACategory).all()
    
    # Add question counts to each category
    for category in categories:
        category.question_count = db.query(QAItem).filter(
            QAItem.category_id == category.id,
            QAItem.is_active == True
        ).count()
    
    return categories


@router.get("/qa", response_model=QASearchResponse)
def get_qa_items(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
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
    query = db.query(QAItem).filter(QAItem.is_active == True).options(joinedload(QAItem.category))
    
    if category_id:
        query = query.filter(QAItem.category_id == category_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                QAItem.question.ilike(search_term), 
                QAItem.answer.ilike(search_term)
            )
        )
    
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    # Add view counts and feedback scores to each item
    for item in items:
        item.view_count = db.query(UserInteraction).filter(
            UserInteraction.qa_item_id == item.id,
            UserInteraction.interaction_type == 'view'
        ).count()
        
        feedback_scores = db.query(UserInteraction.feedback_score).filter(
            UserInteraction.qa_item_id == item.id,
            UserInteraction.interaction_type == 'feedback',
            UserInteraction.feedback_score.isnot(None)
        ).all()
        
        if feedback_scores:
            item.feedback_score = sum(score[0] for score in feedback_scores) / len(feedback_scores)
        else:
            item.feedback_score = 0.0
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }


@router.post("/feedback")
def submit_feedback(
    feedback: UserFeedback,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit user feedback on a Q&A item.
    
    Args:
        feedback: User feedback data (qa_item_id, feedback_score, feedback_comment)
        
    Returns:
        Success message
    """
    # Validate feedback score
    if feedback.feedback_score and (feedback.feedback_score < 1 or feedback.feedback_score > 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback score must be between 1 and 5"
        )
    
    interaction = UserInteraction(
        user_id=current_user.id,
        qa_item_id=feedback.qa_item_id,
        interaction_type="feedback",
        feedback_score=feedback.feedback_score,
        feedback_comment=feedback.feedback_comment,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")
    )
    
    db.add(interaction)
    db.commit()
    
    return {"success": True, "message": "Feedback submitted successfully"}


@router.get("/popular")
def get_popular_questions(
    limit: int = 10,
    timeframe: Optional[str] = "all",
    db: Session = Depends(get_db)
):
    """
    Get most popular questions based on view count.
    
    Args:
        limit: Number of popular items to return (default: 10)
        timeframe: Timeframe for popularity (day, week, month, all)
        
    Returns:
        List of popular questions with view counts
    """
    query = db.query(
        QAItem.id,
        QAItem.question,
        QACategory.name.label("category"),
        func.count(UserInteraction.id).label("view_count")
    ).join(
        QACategory, QAItem.category_id == QACategory.id
    ).outerjoin(
        UserInteraction, 
        or_(
            UserInteraction.qa_item_id == QAItem.id,
            UserInteraction.interaction_type == 'view'
        )
    ).filter(
        QAItem.is_active == True
    ).group_by(
        QAItem.id, QAItem.question, QACategory.name
    ).order_by(
        desc(func.count(UserInteraction.id))
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
        
        query = query.filter(UserInteraction.created_at >= start_time)
    
    results = query.limit(limit).all()
    
    return [{
        "id": item.id,
        "question": item.question,
        "category": item.category,
        "view_count": item.view_count
    } for item in results]


@router.post("/search", response_model=QASearchResponse)
def search_qa(
    search_request: QASearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search Q&A items by query.
    
    Args:
        search_request: Search request with query and filters
        
    Returns:
        Search results with relevance information
    """
    query = db.query(QAItem).filter(QAItem.is_active == True).options(joinedload(QAItem.category))
    
    if search_request.query:
        search_term = f"%{search_request.query}%"
        query = query.filter(
            or_(
                QAItem.question.ilike(search_term), 
                QAItem.answer.ilike(search_term)
            )
        )
    
    if search_request.category_ids:
        query = query.filter(QAItem.category_id.in_(search_request.category_ids))
    
    total = query.count()
    results = query.limit(search_request.limit or 10).all()
    
    # Format results with additional information
    formatted_results = []
    for item in results:
        formatted_results.append({
            "id": item.id,
            "question": item.question,
            "answer_preview": item.answer[:200] + "..." if len(item.answer) > 200 else item.answer,
            "category": item.category.name if item.category else "General",
            "relevance_score": 1.0  # Placeholder for future relevance algorithm
        })
    
    return {
        "total": total,
        "results": formatted_results
    }