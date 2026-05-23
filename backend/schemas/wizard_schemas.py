"""
Pydantic schemas for Wizard Utility API.

This module defines the data models for request/response payloads
in the wizard utility API endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class QACategoryBase(BaseModel):
    """Base schema for Q&A categories."""
    name: str
    description: Optional[str] = None


class QACategoryCreate(QACategoryBase):
    """Schema for creating Q&A categories."""
    pass


class QACategoryResponse(QACategoryBase):
    """Schema for Q&A category responses."""
    id: int
    created_at: datetime
    question_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class QAItemBase(BaseModel):
    """Base schema for Q&A items."""
    question: str
    answer: str
    category_id: Optional[int] = None


class QAItemCreate(QAItemBase):
    """Schema for creating Q&A items."""
    pass


class QAItemUpdate(BaseModel):
    """Schema for updating Q&A items."""
    question: Optional[str] = None
    answer: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class QAItemResponse(QAItemBase):
    """Schema for Q&A item responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    category: Optional[QACategoryResponse] = None
    view_count: Optional[int] = 0
    feedback_score: Optional[float] = 0.0
    
    class Config:
        from_attributes = True


class UserFeedback(BaseModel):
    """Schema for user feedback on Q&A items."""
    qa_item_id: int
    feedback_score: int
    feedback_comment: Optional[str] = None


class QASearchRequest(BaseModel):
    """Schema for Q&A search requests."""
    query: str
    limit: Optional[int] = 10
    category_ids: Optional[List[int]] = None


class QASearchResponse(BaseModel):
    """Schema for Q&A search responses."""
    total: int
    results: List[QAItemResponse]