from typing import Dict, Optional, Any, List
from pydantic import BaseModel

class BaseDataRequest(BaseModel):
    form_data: Dict[str, str]
    project_description: str

class SectionRequest(BaseModel):
    section: str
    proposal_id: str

class RegenerateRequest(BaseModel):
    section: str
    concise_input: str
    proposal_id: str

class GeneratedSection(BaseModel):
    generated_content: Optional[str] = None
    evaluation_status: Optional[str] = None
    feedback: Optional[str] = None

class SaveDraftRequest(BaseModel):
    session_id: Optional[str] = None
    proposal_id: Optional[str] = None
    form_data: Dict[str, str]
    project_description: str
    generated_sections: Optional[Dict[str, GeneratedSection]] = {}
    status: Optional[str] = 'draft'
    donors: Optional[List[str]] = []
    outcomes: Optional[List[str]] = []
    field_contexts: Optional[List[str]] = []

class FinalizeProposalRequest(BaseModel):
    proposal_id: str

class KnowledgeCard(BaseModel):
    id: int
    category: str
    title: str
    summary: Optional[str]
    last_updated: str

class ProposalOut(BaseModel):
    proposal_id: str
    project_title: str
    summary: Optional[str]
    created_at: str
    updated_at: str
    is_accepted: bool
    status: Optional[str]
    donors: List[str]
    outcomes: List[str]
    field_contexts: List[str]
    is_sample: bool = False
