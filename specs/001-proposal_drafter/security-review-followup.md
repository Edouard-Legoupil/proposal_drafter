---
document_type: security-review
review_type: followup
assessment_date: 2025-05-13
codebase_analyzed: Proposal Drafter
total_files_analyzed: 2
total_findings: 12
overall_risk: MODERATE
critical_count: 0
high_count: 3
medium_count: 6
low_count: 3
informational_count: 0
owasp_categories: [A01, A02, A03, A05, A06, A07, A09]
cwe_ids: [CWE-284, CWE-287, CWE-327, CWE-532, CWE-770, CWE-778, CWE-798, CWE-942, CWE-1104]
field_summaries:
  document_type: "Always 'security-review'. Allows indexers to skip non-review documents."
  review_type: "Which command generated this document: audit, branch, staged, plan, tasks, or followup."
  assessment_date: "ISO 8601 date the review was performed (YYYY-MM-DD)."
  overall_risk: "Highest severity tier with active findings (CRITICAL, HIGH, MODERATE, LOW, INFORMATIONAL)."
  critical_count: "Number of Critical findings (CVSS 9.0-10.0)."
  high_count: "Number of High findings (CVSS 7.0-8.9)."
  medium_count: "Number of Medium findings (CVSS 4.0-6.9)."
  low_count: "Number of Low findings (CVSS 0.1-3.9)."
  informational_count: "Number of Informational findings."
  owasp_categories: "OWASP Top 10 2025 categories (A01-A10) that have at least one finding."
  cwe_ids: "CWE identifiers referenced in this document."
  finding_id: "Unique finding identifier (SEC-NNN) for cross-referencing and task linkage."
  location: "File path and line number of the vulnerable code (path/to/file.ext:line)."
  owasp_category: "OWASP Top 10 2025 category for this finding (AXX:2025-Name)."
  cwe: "Common Weakness Enumeration identifier with short name (CWE-NNN: Name)."
  cvss_score: "CVSS v3.1 base score (0.0-10.0). 9.0+=Critical, 7.0-8.9=High, 4.0-6.9=Medium, 0.1-3.9=Low."
  spec_kit_task: "Spec-Kit task ID for backlog tracking and remediation follow-up (TASK-SEC-NNN)."
---

# Security Review Follow-Up Plan: Proposal Drafter

## Executive Summary

**Assessment Date:** 2025-05-13
**Codebase:** Proposal Drafter
**Source Review:** [security-review-plan.md](security-review-plan.md)
**Total Findings:** 12
**Overall Risk:** MODERATE

**Status:** All 12 findings require action. 0 already covered, 0 deferred as technical debt, 12 require implementation.

This follow-up plan converts the 12 security findings from the plan review into actionable tasks. All HIGH and MEDIUM severity findings are prioritized for immediate remediation before production deployment. LOW severity findings are recommended for the next development cycle.

---

## Inputs Reviewed

| Input | Location | Status |
|-------|----------|--------|
| Security Review Report | [security-review-plan.md](security-review-plan.md) | ✅ Reviewed |
| Existing Tasks | `.specify/memory/task.md` | ✅ Reviewed |
| Implementation Plan | [plan.md](plan.md) | ✅ Reviewed |
| Research Report | [research.md](research.md) | ✅ Reviewed |
| Data Model | [data-model.md](data-model.md) | ✅ Reviewed |

---

## Resolution Decisions

### Immediate Remediation (12 items)

All findings require implementation. None are already covered by existing tasks, and none are safe to defer as technical debt given the project's security requirements.

### Already Covered

**None** - The existing task list in `.specify/memory/task.md` focuses on feature development (Qualification System, Budget Builder, Reporting Toolkit) and does not address the security findings identified in the plan review.

### Technical Debt

**None** - All findings, even LOW severity, should be addressed before production deployment given the system's handling of sensitive UN/NGO data and authentication requirements.

---

## 🚨 Immediate Remediation Tasks (HIGH Priority)

### Task ID: TASK-SEC-001
**Title:** Implement Object-Level Authorization for All Resources
**Severity:** HIGH
**Type:** Implement
**OWASP Category:** A01:2025-Broken Access Control
**CWE:** CWE-284: Improper Access Control
**CVSS Score:** 7.5
**Source Finding:** SEC-001
**Depends On:** None
**Location:** All API endpoints accessing user-specific resources

**Description:**
Implement object-level authorization checks in all API endpoints to prevent users from accessing resources they don't own. Currently, the system lacks explicit checks for proposal, knowledge card, and template ownership.

**Acceptance Criteria:**
- [ ] All API endpoints verify user ownership before returning data
- [ ] Authorization middleware checks: user ownership, required permissions, team/donor group membership
- [ ] Integration tests for cross-user access scenarios (must fail with 403 Forbidden)
- [ ] Updated contracts/README.md with authorization requirements for each endpoint
- [ ] Updated data-model.md with authorization relationships

**Implementation Notes:**
- Create `authorization.py` middleware in `backend/core/`
- Add decorators for `@require_ownership`, `@require_permission(permission)`, `@require_team_membership`
- Apply to all endpoints in `backend/api/*.py`
- Test with: user A tries to access user B's proposal via direct ID manipulation

**Effort:** 3-5 days
**Priority:** CRITICAL - Blocking for production

---

### Task ID: TASK-SEC-002
**Title:** Implement Production-Grade Secrets Management
**Severity:** HIGH
**Type:** Implement
**OWASP Category:** A02:2025-Security Misconfiguration
**CWE:** CWE-287: Improper Authentication
**CVSS Score:** 7.3
**Source Finding:** SEC-002
**Depends On:** None
**Location:** Backend configuration and deployment

**Description:**
Implement a secrets management service (Azure Key Vault, Google Secret Manager, or HashiCorp Vault) for production deployment. Current use of environment variables lacks rotation, encryption at rest, and audit logging.

**Acceptance Criteria:**
- [ ] Secrets management service integrated for production
- [ ] Pre-commit hooks prevent secrets from being committed to Git
- [ ] Secrets rotation policy implemented (90-day rotation)
- [ ] Secrets encrypted at rest using KMS or equivalent
- [ ] Audit logging for all secrets access
- [ ] Updated quickstart.md with production secrets configuration
- [ ] Documentation of secrets management procedures in plan.md

**Implementation Notes:**
- Integrate with Azure Key Vault (preferred for Azure deployments)
- Use `python-dotenv` for development, Key Vault for production
- Implement Git pre-commit hooks using `pre-commit` package
- Create `secrets-rotation.sh` script for automated rotation
- Add `.env` to `.gitignore` and implement `.env.example` pattern

**Effort:** 2-3 days
**Priority:** CRITICAL - Blocking for production

---

### Task ID: TASK-SEC-003
**Title:** Standardize Secure Error Handling
**Severity:** HIGH
**Type:** Implement
**OWASP Category:** A10:2025-Mishandling of Exceptional Conditions
**CWE:** CWE-798: Hard-coded Credentials
**CVSS Score:** 7.0
**Source Finding:** SEC-003
**Depends On:** None
**Location:** All API endpoints and error handlers

**Description:**
Implement standardized error handling that prevents information disclosure. Current error responses may expose internal system details, database schema, or file paths that could aid attackers.

**Acceptance Criteria:**
- [ ] All error messages standardized to avoid information disclosure
- [ ] Consistent error handling that doesn't reveal internal details
- [ ] Same error message for all authentication failures ("Invalid credentials")
- [ ] Detailed errors logged server-side without exposing to clients
- [ ] Error handling specification added to contracts/README.md
- [ ] Circuit breakers and graceful degradation for LLM failures implemented
- [ ] Security-focused error tests added

**Implementation Notes:**
- Create `error_handlers.py` in `backend/core/`
- Define error code taxonomy (VALIDATION_ERROR, UNAUTHORIZED, FORBIDDEN, etc.)
- Create `AppException` base class with safe error messages
- Implement `error_response()` helper that sanitizes error details
- Add error logging middleware that logs full details server-side
- Test: verify stack traces never appear in production responses

**Effort:** 2-3 days
**Priority:** CRITICAL - Blocking for production

---

## ⚠️ Medium Priority Remediation Tasks

### Task ID: TASK-SEC-004
**Title:** Implement LLM Prompt Injection Prevention
**Severity:** MEDIUM
**Type:** Implement
**OWASP Category:** A05:2025-Injection
**CWE:** CWE-942: Overly Permissive Cross-domain Whitelist
**CVSS Score:** 6.5
**Source Finding:** SEC-004
**Depends On:** TASK-SEC-003 (Error Handling)
**Location:** All LLM prompt construction in backend

**Description:**
Implement prompt sanitization to prevent prompt injection attacks. User input must be sanitized before being passed to LLM prompts to prevent manipulation of system instructions.

**Acceptance Criteria:**
- [ ] Prompt templates separate user input from system instructions
- [ ] All user input sanitized before inserting into prompts
- [ ] Output validation detects and filters prompt injection attempts
- [ ] Prompt sanitization approach documented in data-model.md
- [ ] Tests for prompt injection resistance added

**Implementation Notes:**
- Create `prompt_sanitizer.py` in `backend/utils/`
- Implement `sanitize_user_input()` function that:
  - Removes or escapes special characters that could manipulate prompts
  - Limits input length
  - Validates input format
- Use parameterized prompts where user input is passed as separate parameters
- Add output validation to detect prompt injection patterns
- Test with known prompt injection attacks

**Effort:** 2-3 days
**Priority:** HIGH

---

### Task ID: TASK-SEC-005
**Title:** Harden Session Management
**Severity:** MEDIUM
**Type:** Implement
**OWASP Category:** A06:2025-Insecure Design
**CWE:** CWE-327: Use of Broken or Risky Cryptographic Algorithm
**CVSS Score:** 6.0
**Source Finding:** SEC-005
**Depends On:** TASK-SEC-002 (Secrets Management)
**Location:** Backend session management (Redis)

**Description:**
Reduce session timeout, implement session regeneration, and improve session security to prevent hijacking and fixation attacks.

**Acceptance Criteria:**
- [ ] Session timeout reduced from 8 hours to 30-60 minutes
- [ ] Session regeneration after authentication (login, password change, privilege escalation)
- [ ] Max session size reduced from 10MB to 1-2MB
- [ ] Cryptographically secure session tokens (minimum 128 bits of entropy)
- [ ] Concurrent session control (limit active sessions per user)
- [ ] Session binding to IP/user-agent (with graceful degradation)
- [ ] Updated research.md with session security specifications

**Implementation Notes:**
- Update Redis session configuration in `backend/core/redis.py`
- Implement session regeneration middleware
- Add session validation on each request
- Implement session store cleanup for expired sessions
- Add rate limiting on session creation

**Effort:** 2 days
**Priority:** HIGH

---

### Task ID: TASK-SEC-006
**Title:** Implement LLM Rate Limiting for Cost Control
**Severity:** MEDIUM
**Type:** Implement
**OWASP Category:** A06:2025-Insecure Design
**CWE:** CWE-770: Allocation of Resources Without Limits
**CVSS Score:** 5.5
**Source Finding:** SEC-006
**Depends On:** None
**Location:** Backend API endpoints for LLM operations

**Description:**
Implement strict rate limiting for LLM endpoints to prevent cost exhaustion, resource exhaustion, and denial of service attacks.

**Acceptance Criteria:**
- [ ] Per-user rate limiting: 5 requests/minute for proposal generation
- [ ] Per-organization rate limiting: 50 requests/minute
- [ ] Global rate limiting: 500 requests/minute
- [ ] Cost-based rate limiting: $10/hour per user limit
- [ ] Budget alerts and automatic suspension when limits exceeded
- [ ] Rate limiting policy documented in plan.md
- [ ] Token bucket or leaky bucket algorithm implemented

**Implementation Notes:**
- Use FastAPI's built-in rate limiting or `slowapi` library
- Implement `RateLimiter` class in `backend/core/rate_limiter.py`
- Track LLM token usage per user/organization
- Add budget tracking and alerting
- Create admin endpoint to view and adjust rate limits
- Test: verify rate limits are enforced and appropriate errors returned

**Effort:** 2 days
**Priority:** HIGH

---

### Task ID: TASK-SEC-007
**Title:** Add Security HTTP Headers
**Severity:** MEDIUM
**Type:** Implement
**OWASP Category:** A02:2025-Security Misconfiguration
**CWE:** CWE-693: Protection Mechanism Failure
**CVSS Score:** 5.3
**Source Finding:** SEC-007
**Depends On:** None
**Location:** Backend middleware

**Description:**
Implement security HTTP headers to protect against common web vulnerabilities including XSS, clickjacking, MIME sniffing, and referrer information leakage.

**Acceptance Criteria:**
- [ ] Content-Security-Policy header implemented
- [ ] X-Frame-Options header implemented (DENY or SAMEORIGIN)
- [ ] X-Content-Type-Options header implemented (nosniff)
- [ ] Strict-Transport-Security header implemented
- [ ] Referrer-Policy header implemented
- [ ] Permissions-Policy header implemented
- [ ] Security headers documented in contracts/README.md
- [ ] Headers tested using securityheaders.com or similar tool

**Implementation Notes:**
- Create `security_headers.py` middleware in `backend/core/`
- Use FastAPI middleware to add headers to all responses
- Configure CSP with appropriate sources for the application
- Set HSTS with max-age=31536000 (1 year)
- Test headers using browser developer tools and securityheaders.com

**Effort:** 1 day
**Priority:** MEDIUM

---

### Task ID: TASK-SEC-008
**Title:** Implement Comprehensive Audit Logging
**Severity:** MEDIUM
**Type:** Implement
**OWASP Category:** A09:2025-Security Logging & Alerting Failures
**CWE:** CWE-778: Insufficient Logging
**CVSS Score:** 5.0
**Source Finding:** SEC-008
**Depends On:** TASK-SEC-001 (Object-Level Authorization)
**Location:** Backend logging infrastructure

**Description:**
Implement comprehensive audit logging for all security-relevant events to enable detection, investigation, and forensics.

**Acceptance Criteria:**
- [ ] All authentication events logged (login, logout, failures)
- [ ] All authorization decisions logged (access granted/denied)
- [ ] All data modifications logged (create, read, update, delete)
- [ ] All sensitive operations logged (proposal generation, knowledge card creation)
- [ ] All security-relevant events logged (rate limit hits, validation failures)
- [ ] Audit log table designed with: timestamp, event type, user ID, IP, user agent, resource, action, outcome
- [ ] Audit logs protected: separate append-only storage, encryption at rest, integrity verification
- [ ] Log monitoring and alerting implemented for suspicious events

**Implementation Notes:**
- Create `audit_logs` table in database
- Create `AuditLogger` class in `backend/core/audit.py`
- Add middleware to log all requests
- Implement `log_auth_event()`, `log_access_decision()`, `log_data_modification()` helpers
- Create log rotation and retention policy
- Integrate with monitoring system (Prometheus/Grafana)

**Effort:** 3-4 days
**Priority:** HIGH

---

## 📋 Low Priority Remediation Tasks

### Task ID: TASK-SEC-009
**Title:** Implement Multi-Factor Authentication
**Severity:** LOW
**Type:** Implement
**OWASP Category:** A07:2025-Authentication Failures
**CWE:** CWE-532: Insertion of Sensitive Information into Log File
**CVSS Score:** 3.7
**Source Finding:** SEC-009
**Depends On:** TASK-SEC-003 (Error Handling)
**Location:** Backend authentication system

**Description:**
Implement multi-factor authentication (TOTP, WebAuthn) to provide additional protection beyond passwords.

**Acceptance Criteria:**
- [ ] MFA implemented as optional feature
- [ ] TOTP support using OTP secrets
- [ ] WebAuthn support for hardware keys
- [ ] Password strength meter with real-time feedback
- [ ] Integration with Have I Been Pwned API for breached password checking
- [ ] Password blacklist for common passwords
- [ ] Authentication security requirements documented in plan.md

**Implementation Notes:**
- Integrate `pyotp` library for TOTP
- Use `webauthn` library for WebAuthn support
- Create MFA setup flow in frontend
- Add MFA verification to login flow
- Store MFA secrets securely (encrypted in database)

**Effort:** 3-5 days
**Priority:** LOW - Nice to have, other auth mechanisms provide protection

---

### Task ID: TASK-SEC-010
**Title:** Implement Dependency Scanning and SBOM Generation
**Severity:** LOW
**Type:** Implement
**OWASP Category:** A03:2025-Software Supply Chain Failures
**CWE:** CWE-1104: Use of Unmaintained Third Party Components
**CVSS Score:** 3.5
**Source Finding:** SEC-010
**Depends On:** None
**Location:** CI/CD pipeline and development workflow

**Description:**
Implement dependency scanning to detect vulnerable or outdated dependencies, and generate Software Bill of Materials (SBOM) for compliance and auditing.

**Acceptance Criteria:**
- [ ] Dependency scanning integrated in CI/CD
- [ ] Vulnerability scanning on every PR
- [ ] PRs blocked with critical/high vulnerabilities
- [ ] All dependency versions pinned (no floating versions)
- [ ] SBOM generated for each release
- [ ] Dependency update policy implemented (monthly updates, security patches within 14 days)
- [ ] Package signature verification before installation
- [ ] Dependency management documented in plan.md

**Implementation Notes:**
- Use GitHub Dependabot or Snyk for scanning
- Generate SBOM using `syft` or `pip-licenses`
- Create `scan-dependencies.sh` script
- Add to GitHub Actions workflow
- Configure alerts for new vulnerabilities

**Effort:** 2-3 days
**Priority:** LOW - Can be implemented iteratively

---

### Task ID: TASK-SEC-011
**Title:** Add Security-Specific Telemetry
**Severity:** LOW
**Type:** Implement
**OWASP Category:** A09:2025-Security Logging & Alerting Failures
**CWE:** CWE-778: Insufficient Logging
**CVSS Score:** 2.0
**Source Finding:** SEC-011
**Depends On:** TASK-SEC-008 (Audit Logging)
**Location:** Backend monitoring infrastructure

**Description:**
Implement security-specific metrics and alerting to detect unusual patterns and respond to security incidents.

**Acceptance Criteria:**
- [ ] Failed authentication attempts tracked
- [ ] Authorization denials tracked
- [ ] Rate limit hits tracked
- [ ] Validation failures tracked
- [ ] Input sanitization events tracked
- [ ] Security dashboards created in Grafana
- [ ] Alerting implemented for security events (brute force, unusual access patterns, config changes)
- [ ] SIEM integration if available

**Implementation Notes:**
- Extend Prometheus metrics with security-specific counters
- Create security dashboards in Grafana
- Implement alert rules for suspicious events
- Set up alerting via Slack/Email/PagerDuty
- Integrate with SIEM if available (Splunk, ELK, etc.)

**Effort:** 2 days
**Priority:** LOW - Can be implemented as part of monitoring infrastructure

---

## ✅ Confirmed Secure Patterns

The following security aspects are already well-implemented and do not require remediation:

| Security Feature | Status | Evidence |
|-----------------|--------|----------|
| JWT Bearer Token Authentication | ✅ Secure | Implemented with refresh tokens |
| Azure AD OAuth 2.0 (EntraID) | ✅ Secure | SSO integration available |
| Secure Session Cookies | ✅ Secure | HTTP-only, Secure flag |
| Password Hashing (PBKDF2) | ✅ Secure | Werkzeug security utils |
| RBAC with 6 Role Types | ✅ Secure | Role-based access control |
| Pydantic Input Validation | ✅ Secure | All API requests validated |
| HTTPS/TLS for Communications | ✅ Secure | Enforced in production |
| Structured LLM Prompts | ✅ Secure | With boundaries and instructions |
| Output Validation | ✅ Secure | JSON parsing, schema validation |
| Grounding with Knowledge Cards | ✅ Secure | Minimizes hallucinations |
| Containerization | ✅ Secure | Docker for all services |
| PostgreSQL with pgvector | ✅ Secure | ACID compliant |

---

## 📊 Task Summary

| Priority | Count | Task IDs |
|----------|-------|----------|
| CRITICAL | 3 | TASK-SEC-001, TASK-SEC-002, TASK-SEC-003 |
| HIGH | 6 | TASK-SEC-004, TASK-SEC-005, TASK-SEC-006, TASK-SEC-007, TASK-SEC-008, TASK-SEC-009 |
| MEDIUM | 3 | TASK-SEC-010, TASK-SEC-011 |
| LOW | 0 | - |

**Total: 12 security remediation tasks**

---

## 🎯 Recommended Implementation Sequence

### Phase 1: Critical Security (Blockers for Production)
1. **TASK-SEC-001** - Object-Level Authorization (3-5 days)
2. **TASK-SEC-002** - Secrets Management (2-3 days)
3. **TASK-SEC-003** - Error Handling (2-3 days)

**Phase 1 Duration:** 1-2 weeks
**Blocked By:** None

### Phase 2: High Security
4. **TASK-SEC-004** - LLM Prompt Injection Prevention (2-3 days)
5. **TASK-SEC-005** - Session Management Hardening (2 days)
6. **TASK-SEC-006** - LLM Rate Limiting (2 days)
7. **TASK-SEC-007** - Security HTTP Headers (1 day)
8. **TASK-SEC-008** - Audit Logging (3-4 days)

**Phase 2 Duration:** 1-2 weeks
**Blocked By:** TASK-SEC-001, TASK-SEC-002 (for some tasks)

### Phase 3: Nice-to-Have Security
9. **TASK-SEC-009** - Multi-Factor Authentication (3-5 days)
10. **TASK-SEC-010** - Dependency Scanning (2-3 days)
11. **TASK-SEC-011** - Security Telemetry (2 days)

**Phase 3 Duration:** 1-2 weeks
**Blocked By:** TASK-SEC-003, TASK-SEC-008

---

## 📝 Next Steps

### Immediate Actions
1. **Review and Approve** this follow-up plan
2. **Prioritize Tasks** based on your team's capacity and deployment timeline
3. **Assign Ownership** for each task to team members
4. **Create Implementation PRs** with appropriate task references

### After Approval
Run `/speckit.security-review.apply` to automatically inject these security tasks into:
- `tasks.md` (as implementation tasks)
- `plan.md` (as security milestones)

### Durable Memory Preservation
Systemic security patterns identified. It is **RECOMMENDED** to execute `/speckit.memory-md.capture` to preserve:
- Object-level authorization pattern
- Secrets management architecture
- Error handling best practices
- LLM security patterns
- Audit logging standards

---

## 📋 Memory Hub INDEX.md Row

```text
| specs/001-proposal_drafter/security-review-followup.md | followup | 2025-05-13 | MODERATE | C:0 H:3 M:6 L:3 | A01,A02,A03,A05,A06,A07,A09 |
```

---

*Generated by `/speckit.security-review.followup` workflow*
