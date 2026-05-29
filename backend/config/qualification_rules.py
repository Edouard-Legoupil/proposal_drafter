# Simplified Qualification Rule Configuration
# This module provides a configurable rule system with priority-based execution

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RuleSeverity(str, Enum):
    """Severity levels for qualification rules"""
    P0 = "P0"  # Critical blockers
    P1 = "P1"  # Major issues
    P2 = "P2"  # Minor issues
    P3 = "P3"  # Informational


class RuleCategory(str, Enum):
    """Categories for qualification rules"""
    BLOCKER = "blocker"  # Hard stop conditions
    COVERAGE = "coverage"  # Completeness requirements
    QUALITY = "quality"  # Quality metrics
    COMPLIANCE = "compliance"  # Regulatory/standard compliance


@dataclass
class QualificationRule:
    """Simplified qualification rule definition"""
    rule_code: str
    rule_name: str
    category: RuleCategory
    severity: RuleSeverity
    applies_to: str  # artifact type (proposal, knowledge_card, template)
    
    # Evaluation configuration
    evaluation_mode: str  # 'hard_blocker', 'threshold', 'score'
    metric_name: Optional[str] = None
    comparator: Optional[str] = None  # '=', '>', '>=', '<', '<='
    threshold_numeric: Optional[float] = None
    threshold_json: Optional[Dict[str, Any]] = None
    
    # Rule metadata
    description: str = ""
    remediation_guidance: str = ""
    is_active: bool = True
    weight: Optional[float] = None  # For scoring rules
    required: bool = True  # Whether this rule must pass


class RuleSet:
    """Configurable rule set for a specific artifact type"""
    
    def __init__(self, name: str, template_type: str, version: str = "v1"):
        self.name = name
        self.template_type = template_type
        self.version = version
        self.rules: List[QualificationRule] = []
        self.is_active = True
    
    def add_rule(self, rule: QualificationRule):
        """Add a rule to this rule set"""
        self.rules.append(rule)
        return self
    
    def get_rules_by_priority(self) -> List[QualificationRule]:
        """Get rules ordered by severity (P0 first, P3 last)"""
        severity_order = {
            RuleSeverity.P0: 0,
            RuleSeverity.P1: 1,
            RuleSeverity.P2: 2,
            RuleSeverity.P3: 3
        }
        return sorted(self.rules, key=lambda r: severity_order[r.severity])
    
    def get_rules_by_category(self, category: RuleCategory) -> List[QualificationRule]:
        """Get rules filtered by category"""
        return [rule for rule in self.rules if rule.category == category]


# Default Rule Sets

def create_default_proposal_rules() -> RuleSet:
    """Create default simplified rule set for proposals"""
    rule_set = RuleSet(
        name="Simplified Proposal Qualification Rules",
        template_type="proposal",
        version="v1"
    )
    
    # P0 Rules (Critical Blockers)
    rule_set.add_rule(QualificationRule(
        rule_code="PROPOSAL_NO_UNRESOLVED_P0",
        rule_name="No unresolved P0 incidents",
        category=RuleCategory.BLOCKER,
        severity=RuleSeverity.P0,
        applies_to="proposal",
        evaluation_mode="hard_blocker",
        metric_name="unresolved_p0_count",
        comparator="=",
        threshold_numeric=0,
        description="Any unresolved P0 incident disqualifies a proposal template",
        remediation_guidance="Resolve all critical incidents and re-run qualification"
    ))
    
    rule_set.add_rule(QualificationRule(
        rule_code="PROPOSAL_MANDATORY_SECTIONS",
        rule_name="Mandatory section completeness",
        category=RuleCategory.BLOCKER,
        severity=RuleSeverity.P0,
        applies_to="proposal",
        evaluation_mode="hard_blocker",
        metric_name="mandatory_section_missing_count",
        comparator="=",
        threshold_numeric=0,
        description="No mandatory section may be missing",
        remediation_guidance="Fix template structure and section planning"
    ))
    
    # P1 Rules (Major Issues)
    rule_set.add_rule(QualificationRule(
        rule_code="PROPOSAL_MIN_SAMPLE_SIZE",
        rule_name="Minimum UAT sample size",
        category=RuleCategory.COVERAGE,
        severity=RuleSeverity.P1,
        applies_to="proposal",
        evaluation_mode="threshold",
        metric_name="uat_sample_size",
        comparator=">=",
        threshold_numeric=5,  # Reduced from 10 for simplicity
        description="At least 5 UAT proposal outputs must be evaluated",
        remediation_guidance="Generate additional UAT proposals and collect reviews"
    ))
    
    rule_set.add_rule(QualificationRule(
        rule_code="PROPOSAL_AVG_SCORE",
        rule_name="Average quality score",
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.P1,
        applies_to="proposal",
        evaluation_mode="threshold",
        metric_name="avg_quality_score",
        comparator=">=",
        threshold_numeric=80,  # Reduced from 85 for simplicity
        description="Average weighted quality score must be at least 80",
        remediation_guidance="Reduce P1/P2 issue frequency and improve section completeness"
    ))
    
    # P2 Rules (Minor Issues)
    rule_set.add_rule(QualificationRule(
        rule_code="PROPOSAL_MIN_SCENARIO_COUNT",
        rule_name="Minimum distinct scenario coverage",
        category=RuleCategory.COVERAGE,
        severity=RuleSeverity.P2,
        applies_to="proposal",
        evaluation_mode="threshold",
        metric_name="distinct_scenario_count",
        comparator=">=",
        threshold_numeric=2,  # Reduced from 3 for simplicity
        description="At least 2 distinct scenarios must be executed",
        remediation_guidance="Add missing donor, geography, and field-context scenarios"
    ))
    
    return rule_set


def create_default_knowledge_card_rules() -> RuleSet:
    """Create default simplified rule set for knowledge cards"""
    rule_set = RuleSet(
        name="Simplified Knowledge Card Qualification Rules",
        template_type="knowledge_card",
        version="v1"
    )
    
    # P0 Rules
    rule_set.add_rule(QualificationRule(
        rule_code="KC_NO_UNRESOLVED_P0",
        rule_name="No unresolved P0 incidents",
        category=RuleCategory.BLOCKER,
        severity=RuleSeverity.P0,
        applies_to="knowledge_card",
        evaluation_mode="hard_blocker",
        metric_name="unresolved_p0_count",
        comparator="=",
        threshold_numeric=0,
        description="Any unresolved P0 incident disqualifies a knowledge card",
        remediation_guidance="Resolve all critical incidents"
    ))
    
    # P1 Rules
    rule_set.add_rule(QualificationRule(
        rule_code="KC_TRACEABILITY",
        rule_name="Source traceability",
        category=RuleCategory.COMPLIANCE,
        severity=RuleSeverity.P1,
        applies_to="knowledge_card",
        evaluation_mode="threshold",
        metric_name="traceable_source_count",
        comparator=">=",
        threshold_numeric=1,
        description="Each knowledge card must have at least one traceable source",
        remediation_guidance="Add proper source references and citations"
    ))
    
    return rule_set


def get_rule_set_for_artifact(artifact_type: str) -> RuleSet:
    """Get the appropriate rule set for an artifact type"""
    if artifact_type == "proposal":
        return create_default_proposal_rules()
    elif artifact_type == "knowledge_card":
        return create_default_knowledge_card_rules()
    else:
        # Default fallback rule set
        rule_set = RuleSet(
            name=f"Default {artifact_type} Qualification Rules",
            template_type=artifact_type,
            version="v1"
        )
        rule_set.add_rule(QualificationRule(
            rule_code=f"{artifact_type.upper()}_NO_UNRESOLVED_P0",
            rule_name="No unresolved P0 incidents",
            category=RuleCategory.BLOCKER,
            severity=RuleSeverity.P0,
            applies_to=artifact_type,
            evaluation_mode="hard_blocker",
            metric_name="unresolved_p0_count",
            comparator="=",
            threshold_numeric=0,
            description="Any unresolved P0 incident disqualifies the artifact",
            remediation_guidance="Resolve all critical incidents"
        ))
        return rule_set