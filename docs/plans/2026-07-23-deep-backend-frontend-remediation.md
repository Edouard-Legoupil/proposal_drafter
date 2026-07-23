# Deep Backend and Frontend Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate the confirmed backend and frontend security, runtime, test, CI, and documentation defects without replacing JWT or breaking supported user workflows.

**Architecture:** Preserve the FastAPI/React structure while moving all access grants behind server-owned policy and approval flows. Repair only API routers that have a supported consumer, consolidate browser requests on cookie authentication, and make regression suites and CI the executable contract for the application.

**Tech Stack:** Python 3, FastAPI, SQLAlchemy, PostgreSQL/SQLite tests, Redis, PyJWT, React, Vite, Material UI, Vitest, Testing Library, ESLint, Pytest, GitHub Actions.

---

### Task 1: Lock down signup and self-service settings

**Files:**
- Modify: `backend/models/schemas.py`
- Modify: `backend/api/auth.py`
- Modify: `backend/api/users.py`
- Test: `backend/tests/test_auth_authorization.py`
- Test: `backend/tests/test_user_settings_authorization.py`

**Steps:**
1. Add endpoint tests proving public signup cannot choose privileged role IDs and self-service updates cannot replace approved roles or team memberships.
2. Run the focused tests and confirm they fail because the current handlers persist client-provided grants.
3. Introduce purpose-specific request schemas. Assign the baseline role on the server and restrict self-service writes to preferences plus pending access requests.
4. Run both focused files, then the existing auth and settings tests.
5. Commit with `fix(auth): prevent self-service privilege grants`.

### Task 2: Harden JWT, cookie, proxy, and authentication failure behavior

**Files:**
- Modify: `backend/core/config.py`
- Modify: `backend/core/middleware.py`
- Modify: `backend/core/rate_limiter.py`
- Modify: `backend/api/auth.py`
- Test: `backend/tests/test_security_configuration.py`
- Test: `backend/tests/test_rate_limiter.py`
- Test: `backend/tests/test_authentication_errors.py`

**Steps:**
1. Add tests for rejecting default production signing keys, `SameSite=Lax` cookies, ignored spoofed forwarding headers, trusted proxies, Redis-backed counters, and uniform invalid-login responses.
2. Run the tests and verify each regression fails for the intended reason.
3. Add environment-aware secret validation, explicit CORS/host/proxy parsing, same-site cookies, trusted-proxy client resolution, and atomic Redis counters with a bounded local fallback.
4. Make invalid username and invalid password responses indistinguishable.
5. Run focused security tests and commit with `fix(security): harden session and request boundaries`.

### Task 3: Enforce knowledge mutation authorization

**Files:**
- Modify: `backend/api/proposals.py`
- Modify: `backend/core/security.py`
- Test: `backend/tests/test_knowledge_mutation_authorization.py`

**Steps:**
1. Add tests showing ordinary authenticated users receive 403 for global donor, outcome, and field-context creation while approved managers succeed.
2. Verify the ordinary-user cases currently fail.
3. Add a reusable role dependency and apply it to every global knowledge mutation endpoint.
4. Run the focused tests and related proposal tests.
5. Commit with `fix(api): restrict global knowledge mutations`.

### Task 4: Repair API router and template-service contracts

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/api/template_management.py`
- Modify: `backend/services/template_service.py`
- Modify or remove from registration: `backend/api/interaction_tracking.py`
- Test: `backend/tests/test_api_route_contract.py`
- Test: `backend/tests/test_template_management.py`

**Steps:**
1. Inventory frontend URL literals and encode each supported method/path as a route-contract test.
2. Run the contract test and record missing routes.
3. Register coherent routers, repair dictionary user dependencies and SQLAlchemy service calls, and exclude unsupported duplicate routers rather than exposing broken endpoints.
4. Add endpoint tests for the repaired template administration paths.
5. Run route and template tests and commit with `fix(api): restore supported backend contracts`.

### Task 5: Isolate and correct backend test infrastructure

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_audit.py`
- Modify: `backend/core/audit.py`
- Modify: affected backend tests that encode obsolete schema assumptions

**Steps:**
1. Add a fixture regression test proving data written by one test is absent from the next and that `team_members.status` exists.
2. Confirm the shared-memory fixture leaks state or lacks the column.
3. Use a per-test SQLite engine with the production-relevant schema and correct the audit-call contract.
4. Run the previously failing access-management and audit tests.
5. Run the complete backend suite with telemetry disabled and commit with `test(backend): isolate database fixtures`.

### Task 6: Fix frontend access panels and settings runtime failures

**Files:**
- Modify: `frontend/src/screens/Admin/resources/ProposalAccessPanel.jsx`
- Modify: `frontend/src/screens/Admin/resources/KnowledgeCardAccessPanel.jsx`
- Modify: `frontend/src/screens/Admin/resources/TemplateAccessPanel.jsx`
- Modify: `frontend/src/components/UserSettingsModal/UserSettingsModal.jsx`
- Modify: `frontend/src/screens/Login/Login.jsx`
- Test: corresponding `*.test.jsx` files

**Steps:**
1. Add render and interaction tests that reach each previously crashing code path.
2. Verify failures for temporal-dead-zone and undefined identifier errors.
3. Reorder hook initialization, connect real loading/status state, remove stale login state, and submit only allowed self-service fields and pending team requests.
4. Run each focused component suite.
5. Commit with `fix(frontend): repair access and settings workflows`.

### Task 7: Protect client routes and unify authenticated requests

**Files:**
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/context/AuthContext.jsx`
- Modify: `frontend/src/utils/api.js`
- Modify: metrics and interaction request modules identified by `rg 'localStorage|Authorization' frontend/src`
- Test: `frontend/src/App.test.jsx`
- Test: `frontend/src/utils/api.test.js`

**Steps:**
1. Add tests proving anonymous users are redirected, non-admin users cannot enter admin screens, and browser API requests use cookies rather than local-storage bearer tokens.
2. Run the tests and verify current behavior fails.
3. Add loading-aware user/admin route guards and route all affected requests through the credentialed API helper.
4. Run focused route, auth-context, and API-helper tests.
5. Commit with `fix(frontend): enforce authenticated navigation`.

### Task 8: Stabilize frontend asynchronous behavior and test suite

**Files:**
- Modify: `frontend/src/components/ChatContainer/ChatContainer.jsx`
- Modify: `frontend/src/hooks/useInteractionTracking.js`
- Modify: `frontend/src/test/setup.js`
- Modify: failing wizard, access, and auth test files

**Steps:**
1. Convert every reported unhandled request or asynchronous assertion into a deterministic failing regression test.
2. Confirm the failures without changing expectations to hide defects.
3. Cancel stale work during unmount, correct hook usage and dependency arrays, add intentional MSW handlers, and replace Jest-only APIs with Vitest APIs.
4. Run the full Vitest suite until it exits cleanly with no unhandled errors.
5. Commit with `test(frontend): stabilize component regressions`.

### Task 9: Clear frontend lint and preserve production compilation

**Files:**
- Modify: frontend source files reported by `npm run lint`
- Modify: `frontend/vite.config.js`
- Test: relevant component and hook tests

**Steps:**
1. Capture the current lint failures and add behavior tests before changing any functional hook or component.
2. Remove dead identifiers, fix invalid hook calls and lexical declarations, and repair the simplified metrics parse error.
3. Add conservative route-level lazy loading or manual chunks only if bundle verification demonstrates the existing warning remains actionable.
4. Run `npm run lint`, `npm run test`, and `npm run build`.
5. Commit with `fix(frontend): restore clean quality checks`.

### Task 10: Gate deployment in CI

**Files:**
- Modify: `.github/workflows/main_dev_propalgen2.yml`

**Steps:**
1. Validate the existing workflow structure and document the absent test dependency as the failing contract.
2. Add backend and frontend quality jobs with dependency caching and make deployment depend on them.
3. Parse the workflow locally and verify every referenced package script exists.
4. Commit with `ci: gate deployment on backend and frontend checks`.

### Task 11: Reconcile documentation with the code

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/SECURITY_OVERVIEW.md`
- Modify: `docs/sso_setup_tutorial.md`
- Modify: `docs/doc_running_local.md`
- Modify: `specs/001-proposal_drafter/plan.md`
- Test: `backend/tests/test_documentation_contract.py`

**Steps:**
1. Add lightweight documentation-contract tests for actual health paths, environment file locations, mandatory OAuth redirects, session lifetime, and real config paths.
2. Confirm the tests fail against current claims.
3. Rewrite claims to match verified code, clearly label historical plans, and remove unsupported security/compliance assertions.
4. Run documentation checks and manually inspect links and commands.
5. Commit with `docs: align operational guidance with the application`.

### Task 12: Final verification and integration

**Files:**
- Modify only files required by regressions discovered during verification.

**Steps:**
1. Run the complete backend suite with a timeout and telemetry disabled.
2. Run frontend tests, lint, and production build from clean dependencies.
3. Run secret scanning, `git diff --check`, and inspect the final branch diff for unrelated changes.
4. Use the requesting-code-review and verification-before-completion workflows; resolve any blocking finding with a new regression test.
5. Commit any final narrowly scoped correction, then integrate the verified commits into `main_dev` and report exact results.
