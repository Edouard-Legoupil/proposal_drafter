#  Standard Library
import uuid
from typing import Dict, Optional, Any

#  Third-Party Libraries
from pydantic import BaseModel

# This module defines the Pydantic models that are used for request and response
# data validation. Pydantic ensures that the data received by the API conforms
# to the expected structure and types.

class BaseDataRequest(BaseModel):
    """
    Schema for the initial data required to start a proposal.
    This includes form data and the main project description.
    """
    form_data: Dict[str, Any]
    project_description: str
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
    proposal_id: uuid.UUID
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


class UpdateSectionRequest(BaseModel):
    """
    Schema for manually updating the content of a single section.
    """
    proposal_id: uuid.UUID
    section: str
    content: str
