from __future__ import annotations

from typing import Any
from crewai import Agent, Task, Crew, Process
from backend.core.config import settings
from backend.utils.prompt_factory import (
    triage_prompt,
    correction_prompt,
    rca_prompt,
    remediation_prompt,
    consistency_prompt,
)
from backend.utils.json_utils import safe_load_json

#import logging
#logger = logging.getLogger(__name__)
#logger = get_logger(__name__)


class IncidentAnalysisCrew:
    def __init__(self):
        self.llm = settings.llm_model

    def _build_agent(self, role: str, goal: str, backstory: str) -> Agent:
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=settings.debug,
            allow_delegation=False,
            llm=self.llm,
        )

    def _run_single_task(self, agent: Agent, description: str) -> dict[str, Any]:
        task = Task(
            description=description,
            expected_output="A valid JSON object and nothing else.",
            agent=agent,
        )
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=settings.debug,
        )
        result = crew.kickoff()
        raw = getattr(result, "raw", None) or str(result)
        return safe_load_json(raw)

    def analyze(self, incident: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
        triage_agent = self._build_agent(
            role="Incident Intake & Triage Agent",
            goal="Normalize incidents, route them correctly, and determine urgency.",
            backstory="You specialize in classification, routing, and review gating for proposal-generation incidents."
        )

        correction_agent = self._build_agent(
            role="Proposal Correction Agent",
            goal="Produce the smallest safe correction for the current artifact.",
            backstory="You help users quickly repair proposals, knowledge cards, and templates without inventing facts."
        )

        rca_agent = self._build_agent(
            role="Root Cause Analysis Agent",
            goal="Determine why the issue occurred and whether it is systemic.",
            backstory="You are expert at tracing proposal-generation failures to retrieval, grounding, template, or validation issues."
        )

        remediation_agent = self._build_agent(
            role="Remediation Agent",
            goal="Recommend durable system fixes to prevent recurrence.",
            backstory="You turn RCA findings into concrete engineering, prompt, data, template, and workflow improvements."
        )

        consistency_agent = self._build_agent(
            role="Consistency & Policy Checker",
            goal="Ensure outputs are mutually consistent and evidence-grounded.",
            backstory="You ensure that user suggestions, RCA findings, and remediation steps do not contradict each other."
        )

        triage_output = self._run_single_task(
            triage_agent,
            triage_prompt(incident=incident, evidence=evidence_pack),
        )

        correction_output = self._run_single_task(
            correction_agent,
            correction_prompt(incident=incident, evidence=evidence_pack),
        )

        rca_output = self._run_single_task(
            rca_agent,
            rca_prompt(incident=incident, evidence=evidence_pack),
        )

        remediation_output = self._run_single_task(
            remediation_agent,
            remediation_prompt(incident=incident, evidence=evidence_pack),
        )

        consistency_output = self._run_single_task(
            consistency_agent,
            consistency_prompt(
                incident=incident,
                evidence=evidence_pack,
                triage_output=triage_output,
                correction_output=correction_output,
                rca_output=rca_output,
                remediation_output=remediation_output,
            ),
        )

        return {
            "triage_output": triage_output,
            "correction_output": correction_output,
            "rca_output": rca_output,
            "remediation_output": remediation_output,
            "consistency_output": consistency_output,
            "agent_versions": {
                "incident_analysis_crew": "v1.0.0",
                "triage_agent": "v1.0.0",
                "correction_agent": "v1.0.0",
                "rca_agent": "v1.0.0",
                "remediation_agent": "v1.0.0",
                "consistency_agent": "v1.0.0",
            },
        }