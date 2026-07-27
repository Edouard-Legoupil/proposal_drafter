"""Canonical static access-role registry.

Roles are deployment code, not tenant-created data. Database rows mirror this
registry so authorization can use stable keys while existing callers may keep
using the legacy numeric ``id`` and display ``name`` columns.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional


@dataclass(frozen=True)
class AccessRole:
    role_key: str
    component: Optional[str]


_ROLE_COMPONENTS = {
    "proposal writer": "ProposalWorkspace",
    "project reviewer": "ReviewWorkspace",
    "knowledge manager donors": "DonorKnowledgeCards",
    "knowledge manager outcome": "OutcomeKnowledgeCards",
    "knowledge manager field context": "FieldContextKnowledgeCards",
    "access_template": "TemplateLibrary",
    "access_metrics": "MetricsDashboard",
    "access_incident": "IncidentDashboard",
    "access_quality_gate": "QualityGate",
    "ui_analysis": "InteractionAnalytics",
    "system admin": None,
    "TEAM_LEADER": None,
}

ROLE_REGISTRY: Mapping[str, AccessRole] = MappingProxyType(
    {role_key: AccessRole(role_key, component) for role_key, component in _ROLE_COMPONENTS.items()}
)

# Compatibility name for callers that describe the registry by its contents.
ACCESS_ROLES = ROLE_REGISTRY
