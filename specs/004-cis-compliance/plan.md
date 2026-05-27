# Implementation Plan: CIS Compliance

**Branch**: `004-cis-compliance` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-cis-compliance/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

This plan implements formal CIS (Center for Internet Security) benchmark compliance for the Proposal Drafter application. The implementation will assess current security configurations against CIS benchmarks, apply recommended hardening measures, implement continuous compliance monitoring, and generate formal compliance documentation.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, PostgreSQL, Docker, CIS-CAT Pro
**Storage**: PostgreSQL with pgcrypto extension
**Testing**: pytest, Playwright
**Target Platform**: Linux server (Ubuntu 22.04 LTS), Docker containers, Azure/GCP cloud
**Project Type**: Web service with React frontend
**Performance Goals**: Maintain current performance while improving security posture
**Constraints**: No downtime during hardening implementation, maintain backward compatibility
**Scale/Scope**: Enterprise web application serving UN agencies and NGOs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file - to be filled during implementation]

## Project Structure

### Documentation (this feature)

```text
specs/004-cis-compliance/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# CIS Compliance Implementation Structure
backend/
├── core/
│   ├── cis_compliance/      # New CIS compliance module
│   │   ├── assessment.py     # CIS assessment functionality
│   │   ├── hardening.py      # Security hardening implementation
│   │   ├── monitoring.py     # Continuous compliance monitoring
│   │   └── reporting.py      # Compliance reporting and documentation
│   └── middleware.py        # Updated with CIS security headers
├── scripts/
│   └── cis_hardening.py     # CIS hardening automation scripts
└── tests/
    └── test_cis_compliance/ # CIS compliance test suite

frontend/
├── src/
│   └── components/
│       └── ComplianceDashboard/ # Compliance monitoring UI
└── tests/
    └── ComplianceDashboard.test.js

docs/
├── security/
│   ├── cis-compliance.md     # CIS compliance documentation
│   └── hardening-guide.md   # Security hardening guide
└── plans/
    └── cis-implementation.md # Implementation plan

.infra/
├── cis-benchmarks/          # CIS benchmark configurations
├── compliance-scans/       # Automated compliance scan scripts
└── monitoring/              # Continuous monitoring configuration
```

**Structure Decision**: The implementation adds a dedicated CIS compliance module to the backend while integrating compliance monitoring into the existing frontend dashboard. This approach minimizes disruption to existing functionality while providing comprehensive CIS compliance capabilities.

## Phase 0: Research & Requirements Resolution

### Research Questions

1. **CIS Benchmark Selection**: Which specific CIS benchmarks apply to our technology stack (Python/FastAPI, PostgreSQL, Docker, Ubuntu 22.04, Azure/GCP)?
2. **Assessment Tools**: What tools are available for CIS benchmark assessment (CIS-CAT Pro alternatives, open-source options)?
3. **Hardening Impact**: What is the expected performance and compatibility impact of applying CIS hardening measures?
4. **Monitoring Integration**: How to integrate CIS compliance monitoring with existing monitoring infrastructure?
5. **Certification Process**: What is the process for formal CIS compliance certification?

### Research Findings

[To be completed during Phase 0 implementation]

## Phase 1: Design & Architecture

### Data Model

**CIS Benchmark Assessment**
```python
class CISAssessment(BaseModel):
    assessment_id: UUID
    timestamp: datetime
    benchmark_version: str
    compliance_score: float  # 0-100%
    total_controls: int
    passed_controls: int
    failed_controls: int
    status: AssessmentStatus  # PENDING, COMPLETE, FAILED
    findings: List[CISFinding]

class CISFinding(BaseModel):
    finding_id: UUID
    control_id: str
    control_description: str
    current_value: str
    expected_value: str
    severity: Severity  # LOW, MEDIUM, HIGH, CRITICAL
    remediation: str
    status: FindingStatus  # PASS, FAIL, UNKNOWN
```

**Security Configuration**
```python
class SecurityConfiguration(BaseModel):
    config_id: UUID
    config_key: str
    config_value: str
    cis_recommendation: str
    compliance_status: ComplianceStatus  # COMPLIANT, NON_COMPLIANT, PENDING
    last_assessed: datetime
    last_modified: datetime
```

**Compliance Alert**
```python
class ComplianceAlert(BaseModel):
    alert_id: UUID
    alert_timestamp: datetime
    severity: AlertSeverity  # INFO, WARNING, CRITICAL
    affected_configuration: str
    current_value: str
    expected_value: str
    remediation_steps: str
    status: AlertStatus  # OPEN, ACKNOWLEDGED, RESOLVED
    resolved_timestamp: Optional[datetime]
```

### Contracts

**API Endpoints**
```
POST /api/cis/assess
- Trigger CIS benchmark assessment
- Returns: assessment_id, status

GET /api/cis/assessments/{assessment_id}
- Get assessment results
- Returns: CISAssessment object

GET /api/cis/configurations
- List all security configurations with compliance status
- Returns: List[SecurityConfiguration]

POST /api/cis/harden
- Apply CIS hardening to specified configurations
- Returns: operation_id, affected_configs

GET /api/cis/alerts
- Get active compliance alerts
- Returns: List[ComplianceAlert]

POST /api/cis/alerts/{alert_id}/resolve
- Resolve a compliance alert
- Returns: success, updated_alert
```

### Quickstart Guide

**CIS Compliance Implementation Quickstart**

1. **Install CIS-CAT Pro or equivalent tool**
   ```bash
   # Download and install CIS assessment tool
   wget https://downloads.cisecurity.org/cis-cat-pro.zip
   unzip cis-cat-pro.zip
   ```

2. **Run initial assessment**
   ```bash
   # Run assessment against current configuration
   python -m backend.scripts.cis_hardening assess --output assessment_report.json
   ```

3. **Review findings and apply hardening**
   ```bash
   # Apply recommended hardening measures
   python -m backend.scripts.cis_hardening harden --config assessment_report.json
   ```

4. **Set up continuous monitoring**
   ```bash
   # Configure automated compliance scans
   python -m backend.scripts.cis_hardening monitor --schedule "0 2 * * *"
   ```

5. **Generate compliance reports**
   ```bash
   # Generate formal compliance documentation
   python -m backend.scripts.cis_hardening report --format pdf --output compliance_report.pdf
   ```

## Phase 2: Implementation Plan

### Implementation Tasks

#### Task 1: CIS Assessment Infrastructure (P1)
- **Objective**: Implement CIS benchmark assessment capability
- **Implementation**:
  - Create CIS assessment module with benchmark parsing
  - Integrate with CIS-CAT Pro or equivalent tool
  - Implement assessment scheduling and result storage
- **Success Criteria**: Can run assessments and store results in database
- **Estimated Time**: 3-5 days

#### Task 2: Security Hardening Automation (P1)
- **Objective**: Implement automated security hardening
- **Implementation**:
  - Create hardening scripts for web server, database, and application
  - Implement safe rollback capability
  - Add pre-hardening backup functionality
- **Success Criteria**: Can apply CIS hardening with rollback option
- **Estimated Time**: 5-7 days

#### Task 3: Compliance Monitoring System (P2)
- **Objective**: Implement continuous compliance monitoring
- **Implementation**:
  - Create monitoring service with scheduled scans
  - Implement alerting system for compliance violations
  - Build compliance dashboard UI integration
- **Success Criteria**: Automated scans run daily with alerting
- **Estimated Time**: 4-6 days

#### Task 4: Compliance Reporting (P2)
- **Objective**: Implement formal compliance reporting
- **Implementation**:
  - Create report generation templates
  - Implement historical trend tracking
  - Add export functionality (PDF, JSON, CSV)
- **Success Criteria**: Can generate audit-ready compliance reports
- **Estimated Time**: 3-4 days

#### Task 5: Documentation and Training (P3)
- **Objective**: Create comprehensive documentation
- **Implementation**:
  - Write CIS compliance guide
  - Create hardening procedures documentation
  - Develop training materials for security team
- **Success Criteria**: Complete documentation set for audits and team training
- **Estimated Time**: 2-3 days

### Testing Strategy

**Unit Tests**: Test individual components (assessment parser, hardening scripts, alerting logic)
**Integration Tests**: Test end-to-end compliance workflow
**Performance Tests**: Verify no significant performance degradation
**Security Tests**: Validate hardening measures are effective
**Compliance Tests**: Verify CIS benchmark compliance is achieved

### Deployment Strategy

1. **Phase 1**: Deploy assessment infrastructure (non-disruptive)
2. **Phase 2**: Run initial assessments and identify hardening targets
3. **Phase 3**: Apply hardening in stages with rollback testing
4. **Phase 4**: Enable continuous monitoring
5. **Phase 5**: Generate initial compliance reports

### Rollback Plan

- Maintain configuration backups before hardening
- Implement feature flags for compliance monitoring
- Provide manual override capability for critical configurations
- Document rollback procedures for each hardening measure

## Success Metrics

- **Compliance Score**: Achieve and maintain 80%+ CIS compliance score
- **Vulnerability Reduction**: 50% reduction in critical security vulnerabilities
- **Detection Time**: Configuration drift detected within 24 hours
- **Remediation Time**: Compliance violations resolved within 2 days
- **Report Generation**: Compliance reports generated in under 5 minutes

## Risks and Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Performance degradation from hardening | Test hardening measures in staging first, implement gradual rollout |
| Configuration conflicts | Maintain comprehensive backups, implement safe rollback procedures |
| Tool compatibility issues | Test multiple assessment tools, have manual assessment fallback |
| Compliance impact on functionality | Test all critical functionality after hardening, maintain backward compatibility |
| Resource constraints | Phase implementation, prioritize critical hardening measures first |

## Open Questions

1. Which specific CIS benchmarks should we prioritize (web server, database, cloud platform)?
2. What is the budget for CIS assessment tools and certification?
3. Are there any existing compliance requirements that conflict with CIS benchmarks?
4. What is the timeline for achieving formal CIS certification?
5. Who will be responsible for ongoing compliance monitoring and maintenance?
