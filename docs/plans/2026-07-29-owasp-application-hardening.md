# OWASP Application Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the application-level OWASP findings for the FastAPI-served React deployment while keeping local authentication available only in development and tests.

**Architecture:** Add environment-aware security configuration at the application boundary, central reusable guards for sessions, remote URLs, uploads, and errors, and install those guards in FastAPI. Preserve current endpoint contracts where safe, but fail closed for production authentication and shared-session failures.

**Tech Stack:** FastAPI, Redis, requests, PyPDF2/pdfplumber, React/Vite, pytest, Vitest, Playwright, npm audit.

---

### Task 1: Environment security contract and production SSO-only mode

**Files:**
- Modify: `backend/core/config.py`
- Modify: `backend/api/auth.py`
- Modify: `backend/.env.example`
- Test: `backend/tests/test_security_configuration.py`
- Test: `backend/tests/test_auth_authorization.py`

**Steps:**

1. Add failing tests that production rejects missing or non-HTTP(S) `SCRAPER_ALLOWED_SCHEMES`, while development defaults to `http,https`.
2. Add failing endpoint tests that production rejects signup, password login, security-question lookup, answer verification, and password update, while SSO endpoints and local test mode remain available.
3. Run the focused tests and confirm failures describe the missing configuration and production authentication gates.
4. Add parsed settings for `SCRAPER_ALLOWED_SCHEMES`, production detection, and local-auth availability. Add one reusable dependency/guard returning `404` or `403` for disabled local authentication and apply it to every local credential endpoint.
5. Document the production variable in `backend/.env.example` and run the focused tests to green.

### Task 2: Redis configuration and fail-closed sessions

**Files:**
- Modify: `backend/core/redis.py`
- Modify: `backend/core/security.py`
- Modify: `backend/api/auth.py`
- Test: `backend/tests/test_session_token_validation.py`
- Test: `backend/tests/test_auth_authorization.py`

**Steps:**

1. Replace the tests that codify fail-open behavior with failing tests expecting `503` when production Redis is unavailable or raises an error. Add URL parsing tests for `redis://` and `rediss://`.
2. Add failing tests that login and SSO callback do not issue an authenticated cookie when the shared session cannot be stored in production.
3. Run these tests and confirm the current hard-coded host and fail-open behavior cause the expected failures.
4. Construct the client from `REDIS_URL`, including TLS URLs. Permit TTL-aware in-memory storage only in development/test; expose a storage-availability function that distinguishes an allowed local fallback from a missing production session store.
5. Make session reads and writes raise a generic `503` in production on unavailable Redis or Redis errors. Preserve `401` for absent/revoked sessions.
6. Run focused session and authentication tests to green.

### Task 3: SSRF-safe, bounded remote scraping

**Files:**
- Modify: `backend/utils/scraper.py`
- Modify: `backend/api/knowledge.py`
- Create: `backend/tests/test_scraper_security.py`
- Modify: `backend/tests/test_knowledge.py`

**Steps:**

1. Add failing unit tests for unsupported schemes, embedded credentials, loopback/private/link-local/reserved IPv4 and IPv6, mixed public/private DNS answers, unsafe redirect targets, excessive redirects, oversized responses, excessive PDF pages, and recursive PDF discovery beyond one hop.
2. Add a positive test for a bounded public HTTP(S) response and a local-development test where the scheme variable is omitted.
3. Run the new tests and confirm the current unrestricted `requests.get` path fails them.
4. Implement URL parsing and DNS validation with `ipaddress` and `socket`; require every resolved address to be globally routable. Disable automatic redirects and validate each `Location` before following it.
5. Stream response chunks up to configurable byte and redirect limits, cap PDF pages and recursion depth, use `urljoin` for relative links, and return a controlled ingestion failure without exposing request-library details.
6. Validate reference URLs at creation/update and again immediately before retrieval to prevent time-of-check/time-of-use and stored-URL bypasses.
7. Run scraper and knowledge tests to green.

### Task 4: Bounded PDF uploads and reliable cleanup

**Files:**
- Modify: `backend/api/proposals.py`
- Modify: `backend/api/knowledge.py`
- Create: `backend/utils/upload_security.py`
- Modify: `backend/tests/test_knowledge.py`
- Modify: `backend/tests/test_generate_document.py`

**Steps:**

1. Add failing tests for oversized uploads, spoofed content types/extensions, missing `%PDF-` signatures, excessive page counts, parser exceptions, and temporary-file cleanup.
2. Run focused tests and confirm current whole-file reads and weak MIME checks fail them.
3. Add a shared chunked upload reader with a strict byte ceiling and PDF signature check. Add a shared page-count guard.
4. Replace unbounded `file.read()` paths, enforce the limits before expensive parsing, and wrap every temporary path in `try/finally` cleanup.
5. Return `413` for size/page limits and `422` for invalid PDFs without raw parser details.
6. Run focused upload tests to green.

### Task 5: Effective rate limiting and public-query bounds

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/core/rate_limiter.py`
- Modify: `backend/api/wizard.py`
- Modify: `backend/api/proposals.py`
- Modify: `backend/api/knowledge.py`
- Test: `backend/tests/test_rate_limiter.py`
- Test: `backend/tests/test_wizard_api.py`
- Test: `backend/tests/test_api_route_contract.py`

**Steps:**

1. Add failing integration tests proving the middleware is installed and repeated expensive requests receive `429` with `Retry-After`.
2. Add failing validation tests that wizard `limit` and pagination values reject negatives and cap large requests.
3. Run focused tests to demonstrate middleware is currently absent and bounds are missing.
4. Register the limiter before request handling, classify generation/ingestion/upload paths separately, and use authenticated user plus trusted client address where available. Fail safely when distributed rate-limit storage is unavailable in production.
5. Add Pydantic/FastAPI query bounds and replace per-item wizard count queries with grouped queries where needed.
6. Run focused tests to green.

### Task 6: Generic production errors with correlation IDs

**Files:**
- Modify: `backend/core/error_handlers.py`
- Modify: `backend/core/middleware.py`
- Modify: `backend/main.py`
- Modify: affected modules under `backend/api/` that return `str(exc)`
- Test: `backend/tests/test_error_handlers.py`
- Test: `backend/tests/test_authentication_errors.py`

**Steps:**

1. Add failing tests that unexpected exceptions and HTTP 5xx details never expose SQL, connector, filesystem, provider, or exception text; assert a correlation ID appears in both response and logs.
2. Add positive tests that safe 4xx validation, authorization, and not-found messages remain usable.
3. Run the tests and confirm the custom HTTP handler currently exposes 5xx detail.
4. Make one registered handler authoritative: preserve safe 4xx details, replace 5xx bodies with a stable message and correlation ID, and log the original exception server-side with that ID.
5. Replace endpoint-created raw exception JSON responses with raised/logged generic failures so they cannot bypass the central handler.
6. Run error and route tests to green.

### Task 7: Secure FastAPI static and SPA delivery

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/core/middleware.py`
- Modify: `backend/tests/test_security_headers.py`
- Create: `backend/tests/test_static_frontend_security.py`

**Steps:**

1. Add failing tests for security headers on index, assets, SPA fallback, redirects, and error responses.
2. Add failing traversal tests using raw and percent-encoded dot segments and assert no file outside `frontend/dist` can be returned.
3. Run the tests and confirm missing containment validation or header gaps.
4. Resolve static candidates with `pathlib.Path.resolve()`, serve them only when they are relative to the resolved frontend root, and otherwise use the SPA index only for valid client routes.
5. Apply the existing CSP, frame, MIME, referrer, permissions, cache, and production HSTS policy consistently to FastAPI static responses. Keep hashed assets cacheable without caching authenticated API responses.
6. Run static and header tests to green.

### Task 8: Frontend navigation and dependency remediation

**Files:**
- Modify: `frontend/src/screens/Chat/components/ChatContainer.jsx`
- Modify: `frontend/src/screens/Chat/components/KnowledgeCard.jsx` or the actual knowledge-card component containing new-window calls
- Create: `frontend/src/utils/safeExternalNavigation.js`
- Create: `frontend/src/utils/safeExternalNavigation.test.js`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

**Steps:**

1. Add failing Vitest cases that reject non-HTTP(S), credential-bearing, and malformed external URLs and assert `window.open` receives `noopener,noreferrer`.
2. Run the focused test and confirm current direct calls fail it.
3. Add one shared navigation helper and replace direct `_blank` calls in the affected components.
4. Run `npm audit`, upgrade React Router and the vulnerable transitive YAML dependency to patched compatible versions, and use lockfile-preserving installation.
5. Run focused tests, the complete frontend test suite, `npm run lint`, `npm run build`, and `npm audit --audit-level=moderate`.

### Task 9: Low-risk disclosure and dependency-scanning closure

**Files:**
- Modify: `backend/api/health.py`
- Modify: `backend/requirements.txt`
- Modify: `.github/workflows/main_dev_propalgen2.yml` or the active CI workflow
- Modify: `backend/tests/test_health_check.py`
- Modify: `backend/tests/test_dependency_scanning.py`

**Steps:**

1. Add failing tests that detailed circuit-breaker state requires an authenticated administrator while basic liveness remains public.
2. Add failing policy tests requiring Python dependency audit and npm audit commands in CI and reproducible frontend installation.
3. Run focused tests and confirm the disclosure and CI gaps.
4. Protect detailed diagnostics, keep a minimal public health response, add `pip-audit`/Bandit and npm audit CI gates, and constrain security-sensitive Python packages without mixing development-only tooling into the production image where practical.
5. Run health and policy tests, then execute the available audits locally.

### Task 10: Full regression and acceptance verification

**Files:**
- Modify only if verification exposes a tested regression.

**Steps:**

1. Run Ruff/Flake8 on changed backend files and ESLint/Prettier checks on changed frontend files.
2. Run the complete backend pytest suite.
3. Run the complete frontend Vitest suite and production build.
4. Start the FastAPI-served production build and run the access-management and authentication Playwright journeys.
5. Run `npm audit --audit-level=moderate`, `pip-audit`, Bandit, and `git diff --check`.
6. Review the final diff against every approved design item, documenting any environmental test limitation instead of claiming unverified completion.
