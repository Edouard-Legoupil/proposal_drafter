# Access Management Compliance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make ordinary component and object access derive strictly from active team membership, team roles, scoped settings, and team object grants, with a complete administrative UI.

**Architecture:** Normalize the existing access tables in place and centralize policy evaluation in a new access service used by authentication, administrative APIs, and protected resource endpoints. Keep `SYSTEM_ADMIN` as the only global direct role, model `TEAM_LEADER` as a member-specific team role, expose an active-team context to React, and replace the fragmented admin editors with team, role, setting, and object-permission views backed by the same policy model.

**Tech Stack:** FastAPI, SQLAlchemy Core/ORM, PostgreSQL/SQLite tests, React 19, Material UI, Vitest/Testing Library, pytest.

---

### Task 1: Normalize the Access Schema and Static Role Registry

**Files:**
- Create: `db/migrations/20260727_access_management_compliance.sql`
- Create: `backend/core/access_roles.py`
- Modify: `db/database-setup.sql`
- Modify: `db/seed.sql`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/test_access_schema.py`

**Step 1: Write failing schema and registry tests**

Assert that the supported registry contains immutable `role_key`/`component` mappings, special roles have no component, membership has status/timestamps, member roles can scope `TEAM_LEADER`, and access settings use `(user_id, team_id, role_key, key)`.

```python
def test_component_roles_have_component_mappings():
    assert ROLE_REGISTRY["proposal writer"].component == "ProposalWorkspace"
    assert ROLE_REGISTRY["system admin"].component is None
    assert ROLE_REGISTRY["TEAM_LEADER"].component is None
```

**Step 2: Run tests and verify RED**

Run: `pytest backend/tests/test_access_schema.py -q`

Expected: FAIL because `backend.core.access_roles` and normalized tables do not exist.

**Step 3: Add the static registry and migration**

Define frozen role records for every role currently used by routes/sidebar: proposal writer, project reviewer, the three knowledge-manager roles, `access_template`, `access_metrics`, `access_incident`, `access_quality_gate`, `ui_analysis`, plus the two special roles. The migration must:

- add team description/creator/timestamps and membership timestamps;
- add `roles.role_key` and `roles.component`, backfill existing names, and reject runtime duplicates;
- create `team_member_roles(team_id, user_id, role_key, assigned_by, assigned_at)` restricted to `TEAM_LEADER`;
- create `access_settings(id, user_id, team_id, role_key, key, value, created_by, updated_at)`;
- convert deterministic ordinary direct assignments into `team_roles`;
- retain only `SYSTEM_ADMIN` in `user_roles` for authorization;
- record ambiguous legacy assignments in a migration-report table instead of widening access.

Update the bootstrap SQL and SQLite test schema to match.

**Step 4: Run tests and verify GREEN**

Run: `pytest backend/tests/test_access_schema.py backend/tests/test_team_roles.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add db/migrations/20260727_access_management_compliance.sql db/database-setup.sql db/seed.sql backend/core/access_roles.py backend/tests/conftest.py backend/tests/test_access_schema.py
git commit -m "feat(access): normalize team access schema"
```

### Task 2: Centralize Active-Team Authorization

**Files:**
- Create: `backend/services/access_management_service.py`
- Modify: `backend/core/security.py`
- Modify: `backend/core/authorization.py`
- Modify: `backend/models/user.py`
- Test: `backend/tests/test_access_context.py`
- Test: `backend/tests/test_backend_security.py`

**Step 1: Write failing context tests**

Cover active-only membership, roles for one selected team only, direct ordinary roles ignored, global admin retained, and leader assignments isolated by team.

```python
def test_direct_ordinary_role_does_not_grant_access(access_service):
    context = access_service.resolve_context("user-1", "team-a")
    assert "access_template" not in context.roles

def test_roles_do_not_leak_between_active_teams(access_service):
    assert access_service.resolve_context("user-1", "team-a").roles == {"access_metrics"}
    assert access_service.resolve_context("user-1", "team-b").roles == {"access_template"}
```

**Step 2: Run tests and verify RED**

Run: `pytest backend/tests/test_access_context.py -q`

Expected: FAIL because current security code unions every direct and inherited role across all teams.

**Step 3: Implement the shared policy service**

Add methods to resolve memberships, select/validate an active team, return roles for that team, check leader scope, load scoped settings, and require component access. Change `get_current_user` to return `memberships`, `active_team`, `roles`, `team_leadership`, and `is_admin`; ordinary `user_roles` must never enter `roles`. Change `require_any_role` and model helpers to evaluate only the selected team context.

**Step 4: Run tests and verify GREEN**

Run: `pytest backend/tests/test_access_context.py backend/tests/test_backend_security.py backend/tests/test_team_roles.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/services/access_management_service.py backend/core/security.py backend/core/authorization.py backend/models/user.py backend/tests/test_access_context.py backend/tests/test_backend_security.py backend/tests/test_team_roles.py
git commit -m "fix(access): enforce active team role context"
```

### Task 3: Complete Team, Membership, Leader, and Role APIs

**Files:**
- Create: `backend/models/access_management.py`
- Create: `backend/api/access_management.py`
- Modify: `backend/main.py`
- Modify: `backend/api/team_membership.py`
- Modify: `backend/api/admin.py`
- Test: `backend/tests/test_access_management_api.py`
- Test: `backend/tests/test_team_membership_api.py`
- Test: `backend/tests/test_api_route_contract.py`

**Step 1: Write failing endpoint tests**

Cover:

- authenticated `GET /api/teams` and `GET /api/roles`;
- admin-only create/update/delete teams;
- conflict-safe team deletion;
- admin add/remove member;
- user join request and pending/active/rejected transitions;
- scoped leader assign/remove;
- leader approval only in their own team;
- admin-only assign/unassign static component roles;
- runtime role creation absent.

**Step 2: Run tests and verify RED**

Run: `pytest backend/tests/test_access_management_api.py backend/tests/test_team_membership_api.py backend/tests/test_api_route_contract.py -q`

Expected: FAIL on missing lifecycle/member/leader routes and overly permissive role endpoints.

**Step 3: Add typed canonical APIs**

Use Pydantic requests instead of dictionaries. Implement:

```text
POST   /api/teams
GET    /api/teams
PATCH  /api/teams/{team_id}
DELETE /api/teams/{team_id}
GET    /api/teams/{team_id}/members
POST   /api/teams/{team_id}/members/{user_id}
DELETE /api/teams/{team_id}/members/{user_id}
POST   /api/teams/{team_id}/join
GET    /api/teams/{team_id}/requests
POST   /api/teams/{team_id}/approve/{user_id}
POST   /api/teams/{team_id}/reject/{user_id}
PUT    /api/teams/{team_id}/leaders/{user_id}
DELETE /api/teams/{team_id}/leaders/{user_id}
GET    /api/roles
GET    /api/teams/{team_id}/roles
POST   /api/teams/{team_id}/roles
DELETE /api/teams/{team_id}/roles/{role_key}
```

Keep old `/admin/teams` creation as a deprecated alias only if required by current callers. Remove `/admin/roles`. Audit every mutation and return 409 for invalid state transitions/dependent team deletion.

**Step 4: Run tests and verify GREEN**

Run: `pytest backend/tests/test_access_management_api.py backend/tests/test_team_membership_api.py backend/tests/test_api_route_contract.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/models/access_management.py backend/api/access_management.py backend/api/team_membership.py backend/api/admin.py backend/main.py backend/tests/test_access_management_api.py backend/tests/test_team_membership_api.py backend/tests/test_api_route_contract.py
git commit -m "feat(access): complete team administration API"
```

### Task 4: Implement User/Team/Role-Scoped Settings

**Files:**
- Modify: `backend/api/access_management.py`
- Modify: `backend/services/access_management_service.py`
- Modify: `backend/core/security.py`
- Test: `backend/tests/test_access_settings_api.py`
- Test: `backend/tests/test_settings_enforcement.py`

**Step 1: Write failing settings tests**

Test admin list/upsert/delete, rejection of a non-member or role not assigned to the team, isolation across teams, and settings loaded only after role authorization.

```python
def test_setting_requires_user_membership_and_team_role(client, admin_override):
    response = client.post("/api/settings", json={
        "user_id": "user-1", "team_id": "team-a",
        "role_key": "access_template", "key": "donor", "value": "ECHO",
    })
    assert response.status_code == 422
```

**Step 2: Run tests and verify RED**

Run: `pytest backend/tests/test_access_settings_api.py backend/tests/test_settings_enforcement.py -q`

Expected: FAIL because the current settings tables do not carry all three scopes.

**Step 3: Implement settings routes and enforcement**

Implement authenticated `GET /api/settings` for the current active context and admin `POST /api/settings` plus `DELETE /api/settings/{setting_id}`. Validate membership and assigned role transactionally. Update data-filter helpers to consume these settings after the role gate.

**Step 4: Run tests and verify GREEN**

Run: `pytest backend/tests/test_access_settings_api.py backend/tests/test_settings_enforcement.py backend/tests/test_user_settings_authorization.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/api/access_management.py backend/services/access_management_service.py backend/core/security.py backend/tests/test_access_settings_api.py backend/tests/test_settings_enforcement.py backend/tests/test_user_settings_authorization.py
git commit -m "feat(access): add scoped access settings"
```

### Task 5: Enforce Team-Only Object Grants and Component Roles

**Files:**
- Modify: `backend/core/authorization.py`
- Modify: `backend/api/admin_resource_access.py`
- Modify: `backend/api/proposals.py`
- Modify: `backend/api/knowledge.py`
- Modify: `backend/api/templates.py`
- Test: `backend/tests/test_admin_resource_access.py`
- Test: `backend/tests/test_object_access_enforcement.py`

**Step 1: Write failing three-gate authorization tests**

For proposals, knowledge cards, and templates, independently prove denial when membership, component role, or team grant is missing. Prove direct user grants and ownership alone do not bypass the three gates for non-admins. Verify read/edit/delete mappings.

**Step 2: Run tests and verify RED**

Run: `pytest backend/tests/test_object_access_enforcement.py backend/tests/test_admin_resource_access.py -q`

Expected: FAIL because current helpers allow owner/direct-user grants and do not require a component role.

**Step 3: Implement the shared object policy**

Replace `_has_explicit_resource_grant` with a single evaluator that requires:

```python
membership.is_active and required_role in active_team.roles and permission in team_grant.permissions
```

Allow only `subject_type="team"` for new object grants, normalize permissions to `read`, `edit`, and `delete`, and ensure resources carry `team_id` and `created_by`/owner. Apply the evaluator to list filtering and individual read/mutate/delete endpoints in all three routers. System administrators remain the only bypass.

**Step 4: Run tests and verify GREEN**

Run: `pytest backend/tests/test_object_access_enforcement.py backend/tests/test_admin_resource_access.py backend/tests/test_backend_security.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/core/authorization.py backend/api/admin_resource_access.py backend/api/proposals.py backend/api/knowledge.py backend/api/templates.py backend/tests/test_admin_resource_access.py backend/tests/test_object_access_enforcement.py
git commit -m "fix(access): enforce team role and object permission gates"
```

### Task 6: Add Active-Team Profile and Switching

**Files:**
- Modify: `backend/api/auth.py`
- Modify: `backend/api/users.py`
- Modify: `backend/models/schemas.py`
- Test: `backend/tests/test_active_team_context.py`

**Step 1: Write failing profile/team-switch tests**

Assert the profile exposes active memberships and only active-team roles; switching rejects non-members/pending members and returns the new scoped roles/settings.

**Step 2: Run tests and verify RED**

Run: `pytest backend/tests/test_active_team_context.py -q`

Expected: FAIL because the profile currently exposes a global role union and no switch operation.

**Step 3: Implement active-team context**

Add `PUT /api/profile/active-team` and persist the selection in the server-side session when Redis is available, with a safe database-backed/default fallback to the first active membership. Remove unauthenticated role discovery and unrestricted team enumeration.

**Step 4: Run tests and verify GREEN**

Run: `pytest backend/tests/test_active_team_context.py backend/tests/test_auth_authorization.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/api/auth.py backend/api/users.py backend/models/schemas.py backend/tests/test_active_team_context.py backend/tests/test_auth_authorization.py
git commit -m "feat(access): expose active team session context"
```

### Task 7: Make Frontend Authorization Active-Team Aware

**Files:**
- Modify: `frontend/src/context/AuthContext.jsx`
- Modify: `frontend/src/components/Base/Base.jsx`
- Modify: `frontend/src/components/Sidebar/Sidebar.jsx`
- Modify: `frontend/src/utils/roleUtils.js`
- Modify: `frontend/src/App.jsx`
- Create: `frontend/src/components/TeamSwitcher.jsx`
- Test: `frontend/src/context/AuthContext.test.jsx`
- Test: `frontend/src/components/Sidebar/Sidebar.test.jsx`
- Test: `frontend/src/utils/roleUtils.test.js`

**Step 1: Write failing rendering/switching tests**

Prove that team switching replaces rather than unions roles, hidden menu items follow active-team roles, protected routes deny missing component roles, and pending memberships cannot be selected.

**Step 2: Run tests and verify RED**

Run: `npm run test -- --run src/context/AuthContext.test.jsx src/components/Sidebar/Sidebar.test.jsx src/utils/roleUtils.test.js`

Working directory: `frontend`

Expected: FAIL because `Base` refetches a separate profile and `Sidebar` uses a disconnected context/global role list.

**Step 3: Implement one frontend auth source**

Extend `AuthContext` with `activeTeam`, `roles`, `memberships`, and `switchTeam`. Make `Base`, `Sidebar`, and route guards consume that context. Add the team switcher and remove default-read/object-owner fallbacks from `roleUtils`.

**Step 4: Run tests and verify GREEN**

Run: `npm run test -- --run src/context/AuthContext.test.jsx src/components/Sidebar/Sidebar.test.jsx src/utils/roleUtils.test.js`

Working directory: `frontend`

Expected: PASS.

**Step 5: Commit**

```bash
git add frontend/src/context/AuthContext.jsx frontend/src/context/AuthContext.test.jsx frontend/src/components/Base/Base.jsx frontend/src/components/Sidebar/Sidebar.jsx frontend/src/components/Sidebar/Sidebar.test.jsx frontend/src/components/TeamSwitcher.jsx frontend/src/utils/roleUtils.js frontend/src/utils/roleUtils.test.js frontend/src/App.jsx
git commit -m "feat(access): scope frontend roles to active team"
```

### Task 8: Rebuild Team and Component-Role Administration

**Files:**
- Modify: `frontend/src/screens/Admin/resources/TeamsAccessPanel.jsx`
- Modify: `frontend/src/components/TeamMembershipManagement.jsx`
- Modify: `frontend/src/hooks/useTeamMembership.js`
- Create: `frontend/src/screens/Admin/components/TeamForm.jsx`
- Create: `frontend/src/screens/Admin/components/RoleAssignmentTable.jsx`
- Test: `frontend/src/screens/Admin/resources/TeamsAccessPanel.test.jsx`
- Test: `frontend/src/components/TeamMembershipManagement.test.jsx`

**Step 1: Write failing admin interaction tests**

Cover search, create/edit/delete, dependent-delete conflict, member add/remove, request approve/reject, leader assign/remove, static roles loaded from the API, component labels displayed, and admin-only role mutation.

**Step 2: Run tests and verify RED**

Run: `npm run test -- --run src/screens/Admin/resources/TeamsAccessPanel.test.jsx src/components/TeamMembershipManagement.test.jsx`

Working directory: `frontend`

Expected: FAIL because the current UI only creates teams and hardcodes five numeric roles.

**Step 3: Implement the team workspace**

Use API-derived role records and explicit loading/error/success states. Separate membership workflow from component-role assignment and label `TEAM_LEADER` as member-scoped. Remove all runtime role creation and direct user-role controls.

**Step 4: Run tests and verify GREEN**

Run: `npm run test -- --run src/screens/Admin/resources/TeamsAccessPanel.test.jsx src/components/TeamMembershipManagement.test.jsx`

Working directory: `frontend`

Expected: PASS.

**Step 5: Commit**

```bash
git add frontend/src/screens/Admin/resources/TeamsAccessPanel.jsx frontend/src/screens/Admin/resources/TeamsAccessPanel.test.jsx frontend/src/components/TeamMembershipManagement.jsx frontend/src/components/TeamMembershipManagement.test.jsx frontend/src/hooks/useTeamMembership.js frontend/src/screens/Admin/components/TeamForm.jsx frontend/src/screens/Admin/components/RoleAssignmentTable.jsx
git commit -m "feat(admin): manage teams members and component roles"
```

### Task 9: Add Settings and Permissions Overview UI

**Files:**
- Modify: `frontend/src/screens/Admin/AccessManagement.jsx`
- Modify: `frontend/src/screens/Admin/resources/UserAccessPanel.jsx`
- Modify: `frontend/src/screens/Admin/components/SubjectPicker.jsx`
- Create: `frontend/src/screens/Admin/resources/AccessOverviewPanel.jsx`
- Create: `frontend/src/screens/Admin/resources/SettingsAccessPanel.jsx`
- Create: `frontend/src/screens/Admin/components/PermissionsMatrix.jsx`
- Modify: `frontend/src/screens/Admin/resources/ProposalAccessPanel.jsx`
- Modify: `frontend/src/screens/Admin/resources/KnowledgeCardAccessPanel.jsx`
- Modify: `frontend/src/screens/Admin/resources/TemplateAccessPanel.jsx`
- Test: `frontend/src/screens/Admin/AccessManagement.test.jsx`
- Test: `frontend/src/screens/Admin/resources/SettingsAccessPanel.test.jsx`
- Test: `frontend/src/screens/Admin/components/PermissionsMatrix.test.jsx`

**Step 1: Write failing admin-workspace tests**

Assert separate Overview, Teams, Settings, Proposals, Knowledge Cards, and Templates sections; searchable matrix; settings scoped by user/team/role; team-only object subjects; and visible read/edit/delete grants.

**Step 2: Run tests and verify RED**

Run: `npm run test -- --run src/screens/Admin/AccessManagement.test.jsx src/screens/Admin/resources/SettingsAccessPanel.test.jsx src/screens/Admin/components/PermissionsMatrix.test.jsx`

Working directory: `frontend`

Expected: FAIL because there is no matrix/settings view and object panels permit user grants.

**Step 3: Implement the consolidated access workspace**

Replace direct-role and legacy focal-list editing in `UserAccessPanel` with membership-centric information. Add accessible matrix markup (table headers and status labels, not color alone), scoped key/value settings controls, and team-only grant pickers for all resource panels.

**Step 4: Run tests and verify GREEN**

Run: `npm run test -- --run src/screens/Admin/AccessManagement.test.jsx src/screens/Admin/resources/SettingsAccessPanel.test.jsx src/screens/Admin/components/PermissionsMatrix.test.jsx src/screens/Admin/resources`

Working directory: `frontend`

Expected: PASS.

**Step 5: Commit**

```bash
git add frontend/src/screens/Admin frontend/src/screens/Admin/AccessManagement.test.jsx
git commit -m "feat(admin): add scoped settings and permissions matrix"
```

### Task 10: Verify Migration, Full Suites, and Documentation

**Files:**
- Modify: `backend/README.md`
- Modify: `docs/access_management_spec.md`
- Modify: `docs/API_DOCUMENTATION.md`
- Create: `playwright/tests/access_management.spec.js`

**Step 1: Add an end-to-end acceptance flow**

Cover admin team creation, member assignment, leader scoping, team role assignment, object grant, team switch, permitted access, and denial after role/grant removal.

**Step 2: Run migration and targeted security checks**

Run: `pytest backend/tests/test_access_schema.py backend/tests/test_access_context.py backend/tests/test_access_management_api.py backend/tests/test_access_settings_api.py backend/tests/test_object_access_enforcement.py -q`

Expected: PASS.

**Step 3: Run complete backend verification**

Run: `pytest backend/tests/ -q`

Expected: PASS.

Run: `ruff check --line-length 120 backend`

Expected: PASS.

**Step 4: Run complete frontend verification**

Run: `npm run test -- --run`

Working directory: `frontend`

Expected: PASS.

Run: `npm run lint`

Working directory: `frontend`

Expected: PASS.

Run: `npm run build`

Working directory: `frontend`

Expected: PASS.

**Step 5: Run the end-to-end flow when services are available**

Run: `pytest playwright/tests/ -q`

Expected: PASS. If local PostgreSQL/Redis/application services are unavailable, report this separately; do not represent unit/build verification as E2E verification.

**Step 6: Update documentation and commit**

Document the static role/component registry, active-team request/response contract, scoped settings, membership transitions, object policy, migration behavior, and admin workflow.

```bash
git add backend/README.md docs/access_management_spec.md docs/API_DOCUMENTATION.md playwright/tests/access_management.spec.js
git commit -m "docs(access): document compliant authorization workflow"
```

**Step 7: Review the requirements checklist**

Re-read `docs/access_management_spec.md` line by line and record evidence for authentication, team management, membership workflow, team roles, settings enforcement, frontend role rendering, object filtering, editing controls, active-team creation, backend enforcement, search, and the permissions matrix.
