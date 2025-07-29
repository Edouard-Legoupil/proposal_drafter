#  Standard Library
from typing import Dict, Optional

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
    form_data: Dict[str, str]
    project_description: str

class SectionRequest(BaseModel):
    """
    Schema for processing a single proposal section.
    Requires the section name and the unique proposal ID.
    """
    section: str
    proposal_id: str

class RegenerateRequest(BaseModel):
    """
    Schema for regenerating a proposal section with new, concise input.
    """
    section: str
    concise_input: str
    proposal_id: str

class SaveDraftRequest(BaseModel):
    """
    Schema for saving a draft of the proposal.
    Includes all proposal data, and can be used for both creating and updating a draft.
    """
    session_id: Optional[str] = None
    proposal_id: Optional[str] = None
    form_data: Dict[str, str]
    project_description: str
    generated_sections: Optional[Dict[str, str]] = {}

class FinalizeProposalRequest(BaseModel):
    """
    Schema for finalizing a proposal, which marks it as complete and read-only.
    """
    proposal_id: str
