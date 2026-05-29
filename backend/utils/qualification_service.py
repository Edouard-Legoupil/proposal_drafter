from __future__ import annotations
import logging
from typing import List, Dict, Any
from backend.config.qualification_rules import get_rule_set_for_artifact, QualificationRule

logger = logging.getLogger(__name__)


class QualificationService:
    """
    Service to run qualification rule evaluation for artifacts (proposal, knowledge_card).
    Uses simplified, configurable rule sets with priority-based execution.
    """

    def __init__(self, connection):
        self.connection = connection

    def run_for_artifact(self, artifact_type: str, artifact_id: str) -> Dict[str, Any]:
        """
        Execute qualification rules against the specified artifact.
        Uses simplified rule sets with priority-based execution.

        Returns:
            Dict with qualification results including overall pass/fail and individual rule results
        """
        try:
            logger.info(f"Running qualification for {artifact_type} {artifact_id}")

            # Get the appropriate rule set for this artifact type
            rule_set = get_rule_set_for_artifact(artifact_type)

            # Execute rules in priority order (P0 first, P3 last)
            results = self._execute_rules_in_priority_order(rule_set, artifact_type, artifact_id)

            # Calculate overall qualification status
            overall_pass = self._calculate_overall_status(results)

            return {
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "rule_set": rule_set.name,
                "rule_set_version": rule_set.version,
                "overall_pass": overall_pass,
                "rule_results": results,
                "executed_at": "CURRENT_TIMESTAMP",  # Would be actual timestamp in real implementation
            }

        except Exception as e:
            logger.error(
                f"Qualification failed for {artifact_type} {artifact_id}: {e}",
                exc_info=True,
            )
            raise

    def _execute_rules_in_priority_order(
        self, rule_set: Any, artifact_type: str, artifact_id: str
    ) -> List[Dict[str, Any]]:
        """Execute rules ordered by severity (P0 first, P3 last)"""
        results = []

        # Get rules in priority order
        rules = rule_set.get_rules_by_priority()

        for rule in rules:
            if not rule.is_active:
                continue

            rule_result = self._evaluate_single_rule(rule, artifact_type, artifact_id)
            results.append(rule_result)

            # For hard blockers, we can stop early if required
            if rule.evaluation_mode == "hard_blocker" and rule.required and not rule_result["passed"]:
                logger.info(f"Hard blocker rule {rule.rule_code} failed, stopping further evaluation")
                break

        return results

    def _evaluate_single_rule(self, rule: QualificationRule, artifact_type: str, artifact_id: str) -> Dict[str, Any]:
        """Evaluate a single qualification rule"""
        try:
            # In a real implementation, this would query metrics from the database
            # For now, we'll simulate the evaluation

            if rule.evaluation_mode == "hard_blocker":
                # Simulate checking for unresolved P0 incidents
                if rule.rule_code == "PROPOSAL_NO_UNRESOLVED_P0":
                    unresolved_p0_count = self._simulate_metric_query(artifact_type, artifact_id, "unresolved_p0_count")
                    passed = unresolved_p0_count == 0

                elif rule.rule_code == "PROPOSAL_MANDATORY_SECTIONS":
                    missing_sections = self._simulate_metric_query(
                        artifact_type, artifact_id, "mandatory_section_missing_count"
                    )
                    passed = missing_sections == 0

                else:
                    # Default hard blocker logic
                    metric_value = self._simulate_metric_query(
                        artifact_type, artifact_id, rule.metric_name or "default_metric"
                    )
                    passed = self._compare_values(metric_value, rule.comparator or "=", rule.threshold_numeric or 0)

            elif rule.evaluation_mode == "threshold":
                metric_value = self._simulate_metric_query(
                    artifact_type, artifact_id, rule.metric_name or "default_metric"
                )
                passed = self._compare_values(metric_value, rule.comparator or ">=", rule.threshold_numeric or 0)

            else:  # score or other modes
                # For scoring rules, we'd calculate a score
                # For now, just simulate a pass
                passed = True

            return {
                "rule_code": rule.rule_code,
                "rule_name": rule.rule_name,
                "severity": rule.severity.value,
                "category": rule.category.value,
                "passed": passed,
                "metric_name": rule.metric_name,
                "metric_value": self._simulate_metric_query(artifact_type, artifact_id, rule.metric_name)
                if rule.metric_name
                else None,
                "threshold": rule.threshold_numeric,
                "comparator": rule.comparator,
                "description": rule.description,
                "remediation": rule.remediation_guidance,
            }

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_code}: {e}")
            return {
                "rule_code": rule.rule_code,
                "rule_name": rule.rule_name,
                "severity": rule.severity.value,
                "passed": False,
                "error": str(e),
            }

    def _simulate_metric_query(self, artifact_type: str, artifact_id: str, metric_name: str) -> float:
        """Simulate querying a metric from the database"""
        # In a real implementation, this would query the actual database
        # For simulation purposes, return some reasonable values

        if metric_name == "unresolved_p0_count":
            return 0  # Assume no P0 incidents for simulation
        elif metric_name == "mandatory_section_missing_count":
            return 0  # Assume all sections present
        elif metric_name == "uat_sample_size":
            return 6  # Assume 6 samples
        elif metric_name == "avg_quality_score":
            return 85  # Assume good quality score
        elif metric_name == "distinct_scenario_count":
            return 3  # Assume 3 scenarios
        elif metric_name == "traceable_source_count":
            return 2  # Assume 2 traceable sources

        return 0  # Default

    def _compare_values(self, value: float, comparator: str, threshold: float) -> bool:
        """Compare a value against a threshold using the specified comparator"""
        if comparator == "=":
            return value == threshold
        elif comparator == ">":
            return value > threshold
        elif comparator == ">=":
            return value >= threshold
        elif comparator == "<":
            return value < threshold
        elif comparator == "<=":
            return value <= threshold
        else:
            return value == threshold  # Default to equality

    def _calculate_overall_status(self, rule_results: List[Dict[str, Any]]) -> bool:
        """Calculate overall qualification status based on rule results"""
        # Overall pass if all required rules pass
        for result in rule_results:
            # If any required rule failed, overall is fail
            if not result.get("passed", False):
                # Check if this was a required rule (in real implementation, we'd have this info)
                # For now, assume all rules are required
                return False
        return True
