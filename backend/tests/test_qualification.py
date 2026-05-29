from backend.config.qualification_rules import get_rule_set_for_artifact, QualificationRule, RuleSeverity
from backend.utils.qualification_service import QualificationService


def test_get_rule_set_for_artifact():
    """Test that we can get appropriate rule sets for different artifact types"""

    # Test proposal rule set
    proposal_rules = get_rule_set_for_artifact("proposal")
    assert proposal_rules.name == "Simplified Proposal Qualification Rules"
    assert proposal_rules.template_type == "proposal"
    assert len(proposal_rules.rules) > 0

    # Test knowledge card rule set
    kc_rules = get_rule_set_for_artifact("knowledge_card")
    assert kc_rules.name == "Simplified Knowledge Card Qualification Rules"
    assert kc_rules.template_type == "knowledge_card"
    assert len(kc_rules.rules) > 0

    # Test fallback rule set
    other_rules = get_rule_set_for_artifact("unknown_type")
    assert "Default" in other_rules.name
    assert other_rules.template_type == "unknown_type"
    assert len(other_rules.rules) > 0


def test_rule_priority_ordering():
    """Test that rules are ordered by severity (P0 first, P3 last)"""
    rule_set = get_rule_set_for_artifact("proposal")
    ordered_rules = rule_set.get_rules_by_priority()

    # Check that rules are in severity order
    severities = [rule.severity for rule in ordered_rules]
    severity_order = {RuleSeverity.P0: 0, RuleSeverity.P1: 1, RuleSeverity.P2: 2, RuleSeverity.P3: 3}

    ordered_severities = [severity_order[s] for s in severities]
    assert ordered_severities == sorted(ordered_severities), "Rules should be ordered by severity"


def test_rule_set_structure():
    """Test that rules have the expected structure"""
    rule_set = get_rule_set_for_artifact("proposal")

    for rule in rule_set.rules:
        assert isinstance(rule, QualificationRule)
        assert hasattr(rule, "rule_code")
        assert hasattr(rule, "rule_name")
        assert hasattr(rule, "category")
        assert hasattr(rule, "severity")
        assert hasattr(rule, "applies_to")
        assert hasattr(rule, "evaluation_mode")
        assert hasattr(rule, "is_active")
        assert hasattr(rule, "description")
        assert hasattr(rule, "remediation_guidance")


def test_qualification_service_simulation():
    """Test that the qualification service can run with simulated data"""
    # Create a mock connection (we'll use None since we're simulating)
    service = QualificationService(None)

    # Test with proposal artifact
    result = service.run_for_artifact("proposal", "test-proposal-123")

    # Check result structure
    assert "artifact_type" in result
    assert "artifact_id" in result
    assert "rule_set" in result
    assert "rule_set_version" in result
    assert "overall_pass" in result
    assert "rule_results" in result
    assert isinstance(result["rule_results"], list)

    # Check that we got some rule results
    assert len(result["rule_results"]) > 0

    # Check individual rule result structure
    for rule_result in result["rule_results"]:
        assert "rule_code" in rule_result
        assert "rule_name" in rule_result
        assert "severity" in rule_result
        assert "category" in rule_result
        assert "passed" in rule_result
        assert isinstance(rule_result["passed"], bool)


def test_hard_blocker_rule_evaluation():
    """Test that hard blocker rules work correctly"""
    service = QualificationService(None)
    result = service.run_for_artifact("proposal", "test-proposal-blocker")

    # Find the hard blocker rule results by checking rule codes we know are blockers
    blocker_rule_codes = ["PROPOSAL_NO_UNRESOLVED_P0", "PROPOSAL_MANDATORY_SECTIONS"]
    blocker_results = [r for r in result["rule_results"] if r["rule_code"] in blocker_rule_codes]

    assert len(blocker_results) > 0, "Should have at least one hard blocker rule"

    # Check that hard blocker rules have the expected structure
    for blocker in blocker_results:
        assert "metric_name" in blocker
        assert "metric_value" in blocker
        assert "threshold" in blocker
        assert "comparator" in blocker


def test_threshold_rule_evaluation():
    """Test that threshold rules work correctly"""
    service = QualificationService(None)
    result = service.run_for_artifact("proposal", "test-proposal-threshold")

    # Find the threshold rule results by checking rule codes we know are thresholds
    threshold_rule_codes = ["PROPOSAL_MIN_SAMPLE_SIZE", "PROPOSAL_AVG_SCORE", "PROPOSAL_MIN_SCENARIO_COUNT"]
    threshold_results = [r for r in result["rule_results"] if r["rule_code"] in threshold_rule_codes]

    assert len(threshold_results) > 0, "Should have at least one threshold rule"

    # Check that threshold rules have the expected structure
    for threshold in threshold_results:
        assert "metric_name" in threshold
        assert "metric_value" in threshold
        assert "threshold" in threshold
        assert "comparator" in threshold


if __name__ == "__main__":
    # Run tests
    test_get_rule_set_for_artifact()
    test_rule_priority_ordering()
    test_rule_set_structure()
    test_qualification_service_simulation()
    test_hard_blocker_rule_evaluation()
    test_threshold_rule_evaluation()
    print("All qualification tests passed!")
