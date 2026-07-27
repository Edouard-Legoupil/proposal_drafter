# Access Management Compliance Design

**Date:** 2026-07-27

**Status:** Approved

## Objective

Bring the administration interface and authorization system into strict compliance with `docs/access_management_spec.md`. Ordinary application access must derive only from active team membership and roles assigned to that team. Legacy direct user roles and the single `users.team_id` relationship must not grant ordinary access.

## Decisions

- `SYSTEM_ADMIN` is the only global role and remains the bootstrap authority for system-wide administration.
- Component roles are static, map explicitly to frontend components, and are assigned to teams.
- `TEAM_LEADER` is assigned to a specific member within a specific team. It grants membership-request authority only for that team.
- Users may be active members of multiple teams and select an active team context.
- Settings are scoped by user, team, and role and are evaluated only after team-role authorization succeeds.
- Object access requires active team membership, the relevant component role, and an explicit object permission for that team.
- Existing access assignments are migrated, but legacy `users.team_id` and ordinary direct `user_roles` are not consulted after migration.

## Data Model

The existing tables will be normalized without replacing unrelated application data.

- `teams` stores `id`, `name`, `description`, `created_by`, and timestamps.
- `team_members` is the authoritative membership relation and stores `user_id`, `team_id`, `status`, and `joined_at`.
- `roles` becomes a static registry containing `role_key` and `component`. Runtime role creation is removed.
- `team_roles` assigns component roles to teams.
- A team-scoped member-role relation assigns `TEAM_LEADER` to individual active memberships.
- Access settings store `user_id`, `team_id`, `role_key`, `key`, and `value` with uniqueness appropriate to that scope.
- Existing resource-grant storage remains the canonical representation of team permissions for proposals, knowledge cards, and templates, provided it exposes read, edit, and delete consistently.

Database migration will translate current team membership and team-role data into the normalized model. Ordinary direct user roles will be converted to team roles where a deterministic active team exists. Ambiguous assignments will be reported rather than silently broadening access.

## Backend Architecture

Authentication remains mandatory for every access-management and resource endpoint. Authorization helpers will resolve:

1. the authenticated user;
2. the requested or active team;
3. active membership in that team;
4. roles assigned to that team;
5. approved settings for the user/team/role scope;
6. object permission when a resource is involved.

System administrators bypass ordinary team checks only for administrative operations. Team leaders can list, approve, and reject pending requests only for teams where they hold the scoped leader assignment. Only system administrators can create, update, or delete teams; assign component roles; assign leaders; directly add or remove members; and configure scoped settings.

The API will provide canonical endpoints for team lifecycle, membership workflow, static role discovery and team assignments, scoped settings, current-user team context, and object grants. Legacy endpoints may remain as narrow aliases during migration, but must call the same authorization and service logic.

Resource endpoints for proposals, knowledge cards, and templates will use shared authorization helpers so list filtering and read/edit/delete operations apply the same three gates: membership, role, and object permission.

## Frontend Architecture

The admin area remains a single access-management workspace with clearly separated sections:

- Overview: searchable counts and a Teams × Roles × Objects permissions matrix.
- Teams: create, edit, delete, select, and inspect teams.
- Memberships: add/remove members, review pending requests, and assign a team-scoped leader.
- Component access: display the static role registry with component mappings and assign/unassign team roles.
- Settings: edit key/value filters for a selected user, team, and role.
- Data access: manage read/edit/delete grants for proposals, knowledge cards, and templates.

The authenticated-user payload will include available teams, the active team, roles for that team, and team-scoped leader information. Sidebar items, routes, and editing controls will derive from that active-team role set. Switching teams reloads the role and settings context. Creation of protected resources records the active team.

Frontend checks improve usability but are never treated as authorization.

## Error Handling and Safety

- Invalid state transitions return conflict responses rather than silently overwriting membership state.
- Cross-team leader actions return forbidden responses.
- Deleting a team with dependent resources requires an explicit conflict-safe policy; the API will not cascade-delete protected objects implicitly.
- Unknown roles and settings outside the selected team/role scope are rejected.
- Administrative mutations are transactional and audited.
- Error responses expose stable user-facing messages without database details.

## Verification Strategy

Implementation follows test-driven development. Backend tests will cover static roles, membership transitions, leader isolation, role inheritance, settings evaluation, active-team context, migration behavior, administrative authorization, and object-level access. Frontend tests will cover the overview matrix, team lifecycle controls, member and leader management, role mappings, scoped settings, team switching, sidebar visibility, filtered objects, and permission-aware editing.

Targeted backend and frontend suites will run after each slice. Final verification will include the complete backend test suite, frontend tests, frontend linting/build, database migration checks, and relevant Playwright flows when the application services are available.
