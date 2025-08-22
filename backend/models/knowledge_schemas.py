from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

class Donor(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        orm_mode = True

class Outcome(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        orm_mode = True

class FieldContext(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        orm_mode = True

class KnowledgeCardReference(BaseModel):
    id: uuid.UUID
    url: str

    class Config:
        orm_mode = True

class KnowledgeCardBase(BaseModel):
    title: str
    summary: Optional[str] = None
    status: Optional[str] = 'draft'
    donor_id: Optional[uuid.UUID] = None
    outcome_id: Optional[uuid.UUID] = None
    field_context_id: Optional[uuid.UUID] = None

class KnowledgeCardCreate(KnowledgeCardBase):
    reference_urls: List[str] = []

class KnowledgeCard(KnowledgeCardBase):
    id: uuid.UUID
    generated_sections: Optional[dict] = None
    is_accepted: bool
    created_at: datetime
    updated_at: datetime
    references: List[KnowledgeCardReference] = []

    class Config:
        orm_mode = True
