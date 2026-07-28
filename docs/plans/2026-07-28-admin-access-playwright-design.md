# Admin Access Playwright Test Design

## Goal

Replace the obsolete administration Playwright suite with browser-driven tests
for every access-management journey documented in
`docs/admin_access_user_journeys.md`.

## Constraints

- All setup and cleanup actions use visible frontend workflows.
- Tests do not use `page.request`, direct HTTP clients, or database access.
- The suite creates its own user, team, proposal, knowledge card, and template
  request through the UI.
- The application has no frontend workflow for creating a grantable template
  record. The template grant scenario therefore requires one seeded template.
- Proposal and knowledge-card creation may invoke long-running AI workflows.

## Test Structure

Use three complementary scenarios in `playwright/tests/test_8_admin.py`:

1. A fast navigation and role-catalog test verifies the seven current Access
   Management tabs, read-only User Access behavior, and all static component
   roles.
2. One slow end-to-end lifecycle creates a unique member, team, role
   assignments, leader assignment, scoped setting, proposal, knowledge card,
   and template request through the UI. The administrator approves the request,
   grants access to the generated resources, checks Overview, runs the Effective
   Access Tester, reviews audit output, and revokes access.
3. A focused seeded-template scenario selects an existing template through the
   UI, grants access, tests effective access, and revokes the grant. It skips
   with a precise prerequisite message if no seeded template exists.

The long lifecycle stays in one test so expensive proposal and knowledge-card
generation happens once. Small smoke assertions remain separate so basic admin
navigation failures are reported quickly.

## Browser Helpers

Keep helpers local to `test_8_admin.py` and make them express user actions:

- register a unique member;
- log in as an administrator or member;
- open an Access Management tab;
- create/select a team;
- add/remove a member and leader;
- assign/remove a component role;
- create/delete a scoped setting;
- create a proposal and knowledge card;
- submit and approve a template request;
- select an admin resource;
- grant, test, and revoke team access.

Helpers use accessible roles, labels, and existing `data-testid` attributes.
They avoid fixed sleeps except where the current long-running UI exposes no
completion event; those flows instead wait for their documented completion
controls with explicit timeouts.

## State and Cleanup

Every mutable entity receives a UUID suffix. Cleanup runs in `finally` blocks
and uses the UI when the relevant deletion control exists. The suite revokes
object grants, deletes settings, removes roles and leaders, removes the member,
and deletes the temporary team. Template requests may remain because the
frontend provides no delete action; their unique names prevent collisions.

## Assertions

The tests verify outcomes visible to an administrator or member:

- current routes and tab headings;
- member and leader badges;
- assigned component-role buttons;
- saved setting table rows;
- created resources in their dashboards and admin pickers;
- granted permissions, Allowed/Denied tester results, and audit entries;
- active-team switching and role-dependent navigation;
- access removal after grant or role revocation.

## Markers and Preconditions

- All scenarios use `admin` and `administrative`.
- The full lifecycle also uses `e2e` and `slow`.
- Admin credentials come from the existing `admin_page` fixture.
- Seed data must include donor, outcome, country, budget, and duration choices
  used by the creation forms.
- The template grant test requires at least one seeded template.
