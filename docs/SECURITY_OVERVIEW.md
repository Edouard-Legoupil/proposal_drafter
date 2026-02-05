# Application Security Measures (OWASP Top 10 Mitigation)

This document summarizes how the app addresses application security concerns, based on secure coding practices and mitigation of the OWASP Top 10 risks.

---

## 1. Input Validation
- **Backend API:** Uses FastAPI with `pydantic` schema models and explicit type hints. All user input is validated for type, format, and boundary conditions before use.
- **Frontend:** UI controls (forms, modals) enforce basic validation (required fields, types). Further server-side checks prevent tampering or bypass.

## 2. Output Encoding & XSS Prevention
- **Markdown/AI/User Content:** All dynamic output rendered as Markdown is sanitized at runtime with `rehype-sanitize` (React). This prevents any malicious HTML or script (XSS) execution, regardless of AI/user input.
- **No raw/unsafe HTML rendering** (never using `dangerouslySetInnerHTML`).

## 3. Injection (SQL, Command, etc.)
- **Database:** Uses SQLAlchemy ORM with strict query parameterization, no string SQL interpolation.
- **No shell command construction from user input.**

## 4. Access Controls (Authorization)
- **Backend:** Every route is protected by dependency injection (`Depends(get_current_user)`), enforcing session/token authentication and per-user/team role checks.
- **Role-Based Access Control (RBAC):** Authorization logic is enforced for each operation (edit, review, manage, etc.).

## 5. Authentication
- **Token/session based auth:** FastAPI. Passwords and secrets are never stored in plaintext. Strong password hashing (bcrypt/PBKDF2/argon2) is used.
- **Session expiration** and re-auth enforced. 

## 6. Cryptographic Best Practices
- **HTTPS enforced** for all app endpoints (App Service and API Gateway level). Secrets are injected via environment variables and never checked-in.
- **No custom cryptography:** Always use proven libraries.

## 7. Secure Dependency Management
- **Frontend:** Uses `npm audit` and automated scripts in CI to scan for known vulnerabilities in React and library deps.
- **Backend:** Uses `pip-audit`, regular pip list --outdated checks. Dependencies are pinned; approved/updated quickly on CVEs.

## 8. Logging and Monitoring
- **Backend:** Critical operations and authentication events are logged. Production must not log sensitive data.
- **Recommendation:** Integrate with a SIEM/log aggregation tool for alerting on breaches or suspicious activity.

## 9. Security Misconfiguration
- **Docker/Env:** Production images do not expose debug info or extra ports. Secure headers configured in hosting environment.
- **CSP/Headers:** CORS and secure response headers set, wherever applicable.

## 10. Data Integrity & SSRF
- **Integrity:** Regular backups, restore testing, and integrity checking as documented in RUNBOOK.md.
- **SSRF:** All third-party outbound fetches are subject to strict allowlisting or blocked; no unvalidated input is used for outbound calls.

---

# Continuous Improvement & Audit
- **Pen-testing:** Regular review of access, input validation, and output encoding practices
- **CI Blockers:** Merges/deploys are blocked if `npm audit` or `pip-audit` detects High/Critical issues
- **Security Awareness:** OWASP Top 10 training required for all engineers

---

For more details, see also:
- `/RUNBOOK.md` (support & backup procedures)
- `/API_METRICS_CONTRACT.md` (API endpoints for monitoring)
