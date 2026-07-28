# Administrator Access Playwright Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the obsolete administration Playwright suite with browser-only coverage of the current access-management journeys.

**Architecture:** Keep all reusable interactions local to `test_8_admin.py` and drive state exclusively through visible frontend controls. Use unique UUID suffixes for mutable records, row-scoped actions for safe cleanup, and current admin resource panels for grants, effective-access testing, audit assertions, and overview assertions.

**Tech Stack:** Python, pytest, Playwright sync API, React/MUI frontend selectors.

---

### Task 1: Map current frontend journeys

**Files:**
- Inspect: `frontend/src/screens/Admin/AccessManagement.jsx`
- Inspect: `frontend/src/screens/Admin/resources/*.jsx`
- Inspect: `frontend/src/components/TeamMembershipManagement.jsx`
- Inspect: `playwright/tests/test_2_proposal_creation.py`
- Inspect: `playwright/tests/test_3_knowledge_card.py`
- Inspect: `playwright/tests/test_6_template_management.py`

**Steps:**
1. Record the current access tabs and URL segments.
2. Record accessible labels, test IDs, and row structure for team, role, setting, resource, grant, tester, and template-request controls.
3. Confirm that setup and cleanup can be performed through the browser UI.

### Task 2: Replace obsolete administration tests

**Files:**
- Modify: `playwright/tests/test_8_admin.py`

**Steps:**
1. Remove incident-resource and direct-user-role-request tests.
2. Add local helpers for authentication, registration, teams, member leadership, component roles, scoped settings, proposal/card/template creation, grants, access testing, and cleanup.
3. Add a fast navigation/read-only user-access test covering every current tab and route.
4. Add the full slow administrator journey using unique browser-created resources.
5. Add the independent seeded-template grant journey with the required exact skip reason.

### Task 3: Keep structured audit events renderable

**Files:**
- Modify: `frontend/src/screens/Admin/components/AuditTimeline.jsx`
- Create: `frontend/src/screens/Admin/components/AuditTimeline.test.jsx`

**Steps:**
1. Reproduce the React failure caused by rendering JSON audit details as a child.
2. Format structured details as readable text without changing existing string details.
3. Correlate each Playwright grant assertion with the newly rendered audit event.

### Task 4: Verify and commit

**Files:**
- Test: `playwright/tests/test_8_admin.py`
- Test: `frontend/src/screens/Admin/components/AuditTimeline.test.jsx`
- Create: `docs/plans/2026-07-28-admin-access-playwright-implementation.md`

**Steps:**
1. Run collection-only pytest.
2. Run Ruff, pre-commit, `git diff --check`, and the forbidden-pattern search.
3. Check whether the configured live application is available; run live tests only when it is available and report honestly otherwise.
4. Review the final diff against every acceptance criterion.
5. Force-add the ignored plan, stage the test, and commit as `test(access): cover administrator frontend journeys`.
