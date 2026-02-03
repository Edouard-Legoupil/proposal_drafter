#  Standard Library
import uuid
from typing import Dict, Optional, Any, List

#  Third-Party Libraries
from pydantic import BaseModel

# This module defines the Pydantic models that are used for request and response
# data validation. Pydantic ensures that the data received by the API conforms
# to the expected structure and types.

class Role(BaseModel):
    id: int
    name: str

class UserRole(BaseModel):
    user_id: uuid.UUID
    role_id: int

class UserDonorGroup(BaseModel):
    user_id: uuid.UUID
    donor_group: str

class UserOutcome(BaseModel):
    user_id: uuid.UUID
    outcome_id: uuid.UUID

class UserFieldContext(BaseModel):
    user_id: uuid.UUID
    field_context_id: uuid.UUID

class UserSettings(BaseModel):
    geographic_coverage_type: Optional[str] = None
    geographic_coverage_region: Optional[str] = None
    geographic_coverage_country: Optional[str] = None
    roles: List[int]
    donor_groups: Optional[List[str]] = None
    outcomes: Optional[List[uuid.UUID]] = None
    field_contexts: Optional[List[uuid.UUID]] = None

class User(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    geographic_coverage_type: Optional[str] = None
    geographic_coverage_region: Optional[str] = None
    geographic_coverage_country: Optional[str] = None
    roles: List[Role] = []
    is_admin: bool = False
    donor_groups: List[str] = []
    outcomes: List[uuid.UUID] = []
    field_contexts: List[uuid.UUID] = []


class BaseDataRequest(BaseModel):
    """
    Schema for the initial data required to start a proposal.
    This includes form data and the main project description.
    """
    form_data: Dict[str, Any]
    project_description: str
    associated_knowledge_cards: Optional[List[Dict[str, Any]]] = None
    template_name: str

class SectionRequest(BaseModel):
    """
    Schema for processing a single proposal section.
    Requires the section name, the unique proposal ID, and the latest
    form data to ensure the generation logic is up-to-date.
    """
    section: str
    proposal_id: uuid.UUID
    form_data: Dict[str, Any]
    project_description: str

class RegenerateRequest(BaseModel):
    """
    Schema for regenerating a proposal section with new, concise input.
    Also includes the latest form data.
    """
    section: str
    concise_input: str
    form_data: Dict[str, Any]
    project_description: str

class GeneratedSection(BaseModel):
    generated_content: Optional[str] = None
    evaluation_status: Optional[str] = None
    feedback: Optional[str] = None

class SaveDraftRequest(BaseModel):
    """
    Schema for saving a draft of the proposal.
    Includes all proposal data, and can be used for both creating and updating a draft.
    """
    session_id: Optional[str] = None
    proposal_id: Optional[uuid.UUID] = None
    template_name: Optional[str] = None
    form_data: Dict[str, Any]
    project_description: str
    generated_sections: Optional[Dict[str, GeneratedSection]] = {}

class FinalizeProposalRequest(BaseModel):
    """
    Schema for finalizing a proposal, which marks it as complete and read-only.
    """
    proposal_id: uuid.UUID

class CreateSessionRequest(BaseModel):
    """
    Schema for creating a new proposal session from the initial form data.
    """
    form_data: Dict[str, Any]
    project_description: str
    associated_knowledge_cards: Optional[List[Dict[str, Any]]] = None


class UpdateSectionRequest(BaseModel):
    """
    Schema for manually updating the content of a single section.
    """
    proposal_id: uuid.UUID
    section: str
    content: str


from datetime import datetime

class PeerReviewerInfo(BaseModel):
    user_id: uuid.UUID
    deadline: Optional[datetime] = None

class SubmitPeerReviewRequest(BaseModel):
    """
    Schema for submitting a proposal for peer review.
    """
    reviewers: list[PeerReviewerInfo]


class ReviewComment(BaseModel):
    section_name: str
    review_text: str
    type_of_comment: str
    severity: str

class SubmitReviewRequest(BaseModel):
    """
    Schema for submitting a peer review.
    """
    comments: list[ReviewComment]

class CreateDonorRequest(BaseModel):
    name: str

class CreateOutcomeRequest(BaseModel):
    name: str

class CreateFieldContextRequest(BaseModel):
    name: str
    geographic_coverage: Optional[str] = None
    category: str

class UpdateProposalStatusRequest(BaseModel):
    status: str

class TransferOwnershipRequest(BaseModel):
    new_owner_id: uuid.UUID

class AuthorResponseRequest(BaseModel):
    author_response: str


class SaveContributionIdRequest(BaseModel):
    contribution_id: str
