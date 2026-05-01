#  Standard Library
import uuid
from typing import Dict, Optional, Any, List
from datetime import datetime

#  Third-Party Libraries
from pydantic import BaseModel


class TemplateBase(BaseModel):
    """Base template model"""
    name: str
    filename: str
    template_type: str
    description: Optional[str] = None
    status: str = "draft"
    is_default: bool = False


class TemplateCreate(TemplateBase):
    """Model for creating a new template"""
    template_data: Dict[str, Any]
    version_notes: Optional[str] = None
    donor_ids: Optional[List[uuid.UUID]] = None


class TemplateUpdate(BaseModel):
    """Model for updating template metadata"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_default: Optional[bool] = None


class TemplateVersionBase(BaseModel):
    """Base template version model"""
    version_number: str
    version_notes: Optional[str] = None
    status: str = "draft"


class TemplateVersionCreate(TemplateVersionBase):
    """Model for creating a new template version"""
    template_data: Dict[str, Any]


class TemplateVersionUpdate(BaseModel):
    """Model for updating template version metadata"""
    version_notes: Optional[str] = None
    status: Optional[str] = None


class TemplateDonor(BaseModel):
    """Model for template-donor mapping"""
    template_id: uuid.UUID
    donor_id: uuid.UUID


class TemplateAuditLog(BaseModel):
    """Model for template audit log entries"""
    action: str
    action_details: Optional[Dict[str, Any]] = None


class TemplateResponse(BaseModel):
    """Response model for template with metadata"""
    id: uuid.UUID
    name: str
    filename: str
    template_type: str
    description: Optional[str] = None
    status: str
    is_default: bool
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_by: Optional[uuid.UUID] = None
    updated_at: datetime
    latest_version: Optional[str] = None
    latest_version_status: Optional[str] = None
    donor_count: int = 0


class TemplateVersionResponse(BaseModel):
    """Response model for template version"""
    id: uuid.UUID
    template_id: uuid.UUID
    version_number: str
    version_notes: Optional[str] = None
    status: str
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_by: Optional[uuid.UUID] = None
    updated_at: datetime


class TemplateFullResponse(BaseModel):
    """Response model for full template with data"""
    template: TemplateResponse
    version: TemplateVersionResponse
    template_data: Dict[str, Any]
    donors: List[Dict[str, Any]] = []