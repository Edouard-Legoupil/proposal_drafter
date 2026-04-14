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
    requested_roles: Optional[List[int]] = []
    donor_groups: Optional[List[str]] = None
    donor_ids: Optional[List[uuid.UUID]] = []
    outcomes: Optional[List[uuid.UUID]] = None
    field_contexts: Optional[List[uuid.UUID]] = None

class User(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    team_name: Optional[str] = None
    geographic_coverage_type: Optional[str] = None
    geographic_coverage_region: Optional[str] = None
    geographic_coverage_country: Optional[str] = None
    roles: List[Role] = []
    is_admin: bool = False
    donor_groups: List[str] = []
    donor_ids: List[uuid.UUID] = []
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
    document_type: Optional[str] = "proposal"
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
    document_type: Optional[str] = "proposal"


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
    review_text: Optional[str] = ""
    type_of_comment: Optional[str] = "General"
    severity: Optional[str] = "Medium"
    rating: Optional[str] = None

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
    feedback_id: Optional[uuid.UUID] = None
    status: Optional[str] = None


class SaveContributionIdRequest(BaseModel):
    contribution_id: str

class CreateTeamRequest(BaseModel):
    name: str

class UpdateUserTeamRequest(BaseModel):
    team_id: uuid.UUID

class DonorTemplateRequestCreate(BaseModel):
    name: str
    donor_id: Optional[uuid.UUID] = None
    donor_ids: Optional[List[uuid.UUID]] = None
    template_type: Optional[str] = "proposal"  # "proposal" or "concept_note"
    configuration: Dict[str, Any]  # {"instructions": [...], "sections": [...]}

class DonorTemplateCommentCreate(BaseModel):
    comment_text: str
    section_name: Optional[str] = None  # None = general comment; set for section-scoped
    rating: Optional[str] = None # 'up' or 'down'
    severity: Optional[str] = None
    type_of_comment: Optional[str] = "Donor Template"

class DonorTemplateStatusUpdate(BaseModel):
    status: str  # pending, approved, rejected, published


### new class for incident

from enum import Enum


class ArtifactType(str, Enum):
    proposal = "proposal"
    knowledge_card = "knowledge_card"
    template = "template"


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


TYPE_OF_COMMENT_OPTIONS = {
    "proposal": {
        "P0": ["Factual Error", "Compliance Violation", "Security Risk"],
        "P1": ["Major Content Gap", "Structural Issue", "Quality Concern"],
        "P2": ["Clarity Issue", "Tone Mismatch", "Minor Gap"],
        "P3": ["Formatting Issue", "Typo", "Style Suggestion"],
    },
    "knowledge_card": {
        "P0": ["Data Integrity", "Source Error", "Critical Omission"],
        "P1": ["Metadata Issue", "Duplicate Content", "Outdated Information"],
        "P2": ["Relevance Issue", "Traceability Gap", "Generic Content"],
        "P3": ["Formatting Issue", "Minor Error", "Style Suggestion"],
    },
    "template": {
        "P0": ["Compliance Issue", "Structural Problem", "Critical Error"],
        "P1": ["Major Quality Issue", "Content Gap", "Format Problem"],
        "P2": ["Clarity Issue", "Tone Mismatch", "Minor Improvement"],
        "P3": ["Formatting Issue", "Typo", "Style Suggestion"],
    },
}


ROOT_CAUSE_PRIORS = {
    "proposal": {
        "Factual Error": ["grounding_failure", "outdated_knowledge", "retrieval_failure"],
        "Compliance Violation": ["policy_guardrail_failure", "template_mapping_failure", "citation_traceability_failure"],
        "Security Risk": ["policy_guardrail_failure", "retrieval_failure", "prompt_instruction_failure"],
        "Major Content Gap": ["template_mapping_failure", "retrieval_failure", "missing_source_content"],
        "Structural Issue": ["template_mapping_failure", "prompt_instruction_failure"],
        "Quality Concern": ["prompt_instruction_failure", "section_planning_failure"],
        "Clarity Issue": ["prompt_instruction_failure"],
        "Tone Mismatch": ["prompt_instruction_failure", "template_mapping_failure"],
        "Minor Gap": ["retrieval_failure", "section_planning_failure"],
        "Formatting Issue": ["post_processing_failure"],
        "Typo": ["post_processing_failure"],
        "Style Suggestion": ["post_processing_failure", "template_mapping_failure"],
    },
    "knowledge_card": {
        "Data Integrity": ["metadata_quality_issue", "missing_source_content"],
        "Source Error": ["citation_traceability_failure", "metadata_quality_issue"],
        "Critical Omission": ["missing_source_content", "outdated_knowledge"],
        "Metadata Issue": ["metadata_quality_issue"],
        "Duplicate Content": ["metadata_quality_issue"],
        "Outdated Information": ["outdated_knowledge"],
        "Relevance Issue": ["retrieval_failure"],
        "Traceability Gap": ["citation_traceability_failure"],
        "Generic Content": ["prompt_instruction_failure"],
        "Formatting Issue": ["post_processing_failure"],
        "Minor Error": ["post_processing_failure"],
        "Style Suggestion": ["post_processing_failure"],
    },
    "template": {
        "Compliance Issue": ["template_mapping_failure", "policy_guardrail_failure"],
        "Structural Problem": ["template_mapping_failure"],
        "Critical Error": ["template_mapping_failure", "validation_failure"],
        "Major Quality Issue": ["template_mapping_failure", "prompt_instruction_failure"],
        "Content Gap": ["template_mapping_failure", "missing_source_content"],
        "Format Problem": ["post_processing_failure", "template_mapping_failure"],
        "Clarity Issue": ["prompt_instruction_failure"],
        "Tone Mismatch": ["prompt_instruction_failure"],
        "Minor Improvement": ["prompt_instruction_failure"],
        "Formatting Issue": ["post_processing_failure"],
        "Typo": ["post_processing_failure"],
        "Style Suggestion": ["post_processing_failure"],
    },
}

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

# Local imports - these are defined earlier in this same file


class IncidentAnalyzeRequest(BaseModel):
    artifact_type: ArtifactType
    severity: Severity
    incident_type: str
    source_review_id: str | None = None

    # direct/manual payload mode
    proposal_id: str | None = None
    knowledge_card_id: str | None = None
    template_request_id: str | None = None

    section_name: str | None = None
    user_comment: str | None = None

    # optional extra context
    generator_run_id: str | None = None
    related_requirement_ids: list[str] = Field(default_factory=list)
    related_knowledge_card_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_incident_type(self):
        allowed = TYPE_OF_COMMENT_OPTIONS[self.artifact_type.value][self.severity.value]
        if self.incident_type not in allowed:
            raise ValueError(
                f"incident_type '{self.incident_type}' is not valid for "
                f"{self.artifact_type.value}/{self.severity.value}. "
                f"Allowed: {allowed}"
            )
        return self


class EvidenceRef(BaseModel):
    id: str
    type: str | None = None
    title: str | None = None
    excerpt: str | None = None
    uri: str | None = None


class TextPatch(BaseModel):
    section_id: str | None = None
    before: str | None = None
    after: str


class AlternativeSuggestion(BaseModel):
    label: Literal["minimal_safe", "preferred", "fallback"]
    summary: str | None = None
    proposed_action: str
    patch: TextPatch | None = None
    confidence: float


class UserSuggestion(BaseModel):
    summary: str
    why: str | None = None
    proposed_action: str
    proposed_replacement: str | None = None
    patch: TextPatch | None = None
    alternatives: list[AlternativeSuggestion] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    confidence: float


class BlastRadius(BaseModel):
    scope: Literal[
        "single_run", "single_proposal", "multiple_proposals",
        "template_wide", "knowledge_base_wide", "unknown"
    ] = "unknown"
    estimated_count: int | None = None
    notes: str | None = None


class Hypothesis(BaseModel):
    cause: str
    reason: str | None = None
    confidence: float


class RootCauseAnalysis(BaseModel):
    primary_cause: str
    secondary_causes: list[str] = Field(default_factory=list)
    explanation: str
    immediate_cause: str | None = None
    systemic_cause: str | None = None
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    blast_radius: BlastRadius | None = None
    confidence: float


class ImplementationTask(BaseModel):
    description: str
    owner: str | None = None
    eta_days: int | None = None


class SuggestedSystemFix(BaseModel):
    category: Literal[
        "prompt_instruction",
        "retrieval_ranking",
        "knowledge_curation",
        "template_design",
        "validation_guardrail",
        "workflow_ux",
        "monitoring_observability",
        "data_pipeline",
        "other",
    ]
    priority: Literal["low", "medium", "high", "critical"]
    owner: str | None = None
    recommendation: str
    implementation_notes: list[str] = Field(default_factory=list)
    implementation_tasks: list[ImplementationTask] = Field(default_factory=list)
    expected_impact: str | None = None
    prevention_type: Literal["preventive", "detective", "corrective", "mixed"] = "mixed"
    confidence: float


class ConsistencyCheck(BaseModel):
    passed: bool = True
    issues: list[str] = Field(default_factory=list)
    policy_flags: list[str] = Field(default_factory=list)


class IncidentAnalysisResponse(BaseModel):
    incident_id: str
    artifact_type: ArtifactType
    severity: Severity
    incident_type: str
    status: str
    source_review_id: str | None = None

    proposal_id: str | None = None
    knowledge_card_id: str | None = None
    template_request_id: str | None = None

    section_name: str | None = None
    user_comment: str | None = None
    normalized_summary: str | None = None

    evidence: dict[str, Any] = Field(default_factory=dict)

    user_suggestion: UserSuggestion
    root_cause_analysis: RootCauseAnalysis
    suggested_system_fix: SuggestedSystemFix

    consistency_check: ConsistencyCheck = Field(default_factory=ConsistencyCheck)

    needs_human_review: bool
    human_review_reason: str | None = None

    routing: dict[str, Any] = Field(default_factory=dict)
    agent_versions: dict[str, str] = Field(default_factory=dict)
    created_at: str
    updated_at: str | None = None


