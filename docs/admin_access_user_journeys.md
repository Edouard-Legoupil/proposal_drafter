# Administrator Guide: Access Management

Use this guide to give users access through the **Access Management** screen.
Access is team-based. Do not assign ordinary roles directly to individual users.

## How access works

For a normal user to access an individual proposal, knowledge card, or template,
all three conditions must be true:

1. The user is an **ACTIVE** member of the team.
2. The team has the required **Component Role**.
3. The team has the required **Access Grant** for that object.

Optional **Settings** can narrow this access by donor, outcome, or field context.
The user's **Active team** determines which membership, roles, and settings apply.
Roles from different teams are never combined.

`SYSTEM_ADMIN` is the only global bypass. Ownership alone does not give a normal
user access, and an object grant never replaces team membership or a role.

## Open Access Management

1. Sign in with a system administrator account.
2. Open the user menu in the top-right corner.
3. Select **Admin**.

The **Access Management** page contains these tabs:

| Tab | Purpose |
|---|---|
| **Overview** | Review team component roles and object grants. |
| **User Access** | Find a user and view their team memberships. This tab is read-only. |
| **Teams** | Create teams, manage members and leaders, and allocate component roles. |
| **Settings** | Apply a donor, outcome, or field-context filter to one user, team, and role. |
| **Proposals** | Grant a team access to a specific proposal. |
| **Knowledge Cards** | Grant a team access to a specific knowledge card. |
| **Templates** | Grant a team access to a specific template. |

## Allocate access to a team

Complete these steps in order.

### 1. Create or select the team

1. Open **Teams**.
2. Select an existing team, or select **Create Team**.
3. For a new team, enter **Team name** and an optional **Description**.
4. Select **Create**.

Use **Edit team** to change its details. Team deletion is blocked while the team
owns protected proposals, knowledge cards, or templates.

### 2. Add members

1. Select the team from the team list.
2. Under **Members**, choose a user in **User to add**.
3. Select **Add member**.

The membership becomes active immediately. You can also process a user's join
request under **Pending Membership Requests** by selecting **Approve** or
**Reject**.

To revoke every permission inherited from this team, select **Remove member**.

### 3. Allocate component roles

Under **Component Roles**, select **Assign ROLE_NAME** for every component the
team needs. A component role applies to every active member of that team.

If two groups of users need different roles, place them in separate teams.
Removing a component role removes that component from every team member.

| Role | Frontend access | Important rule |
|---|---|---|
| `proposal writer` | Proposal workspace and proposal creation | Can read, edit, or delete a granted proposal. |
| `project reviewer` | Review workspace | Can read a granted proposal, but cannot edit or delete it. |
| `knowledge manager donors` | Donor knowledge cards | Access can be narrowed with a `donor` setting. |
| `knowledge manager outcome` | Outcome knowledge cards | Access can be narrowed with an `outcome` setting. |
| `knowledge manager field context` | Field-context knowledge cards | Access can be narrowed with a `field_context` setting. |
| `access_template` | Donor template library | Requires a template grant for a specific template. |
| `access_metrics` | Metrics dashboard | Component role only; no object grant is required. |
| `access_incident` | Incident dashboard | Component role only. |
| `access_quality_gate` | Quality Gate | Component role only. |
| `ui_analysis` | Interaction analytics | Component role only. |

Two special roles do not appear in the component-role table:

- `SYSTEM_ADMIN` has global access and is not allocated to a team.
- `TEAM_LEADER` is assigned to an individual member, not to the whole team.

### 4. Assign a team leader when needed

Under **Members**, select **Make leader** beside a member. A team leader can view,
approve, and reject membership requests only for that team when it is active.
Select **Remove leader** to revoke this responsibility.

`TEAM_LEADER` does not grant proposal, knowledge-card, template, or administrator
access.

### 5. Add a scoped setting when needed

Skip this step when every member with the team role may access all matching data.
A setting only narrows access; it does not grant access.

1. Open **Settings**.
2. Select the **User**, **Team**, and **Role**.
3. Enter one canonical **Setting key**:
   - `donor`
   - `outcome`
   - `field_context`
4. Enter the matching donor, outcome, or field-context identifier as the
   **Setting value**.
5. Select **Save setting**.

Use **Delete** in the settings table to remove a filter. The selected user must
be an active team member, and the selected role must already be assigned to the
team.

### 6. Grant access to individual objects

Complete this step for proposals, knowledge cards, and templates.

1. Open **Proposals**, **Knowledge Cards**, or **Templates**.
2. Select the object to manage.
3. Under **Grant Access**, select the team.
4. Select one or more permissions:
   - **Read**: view or use the object.
   - **Edit**: update the object.
   - **Delete**: delete the object.
5. Select **Save Grant**.

Only teams can receive object grants. To remove a grant, select **Revoke** beside
it. Proposal reviewers remain read-only even if their team grant includes
**Edit** or **Delete**.

Object creation has no separate grant. A user creates an object for their active
team when that team has the required component role.

### 7. Verify the result

Use both checks before telling the user that access is ready:

1. Open **Overview** and confirm the team has the expected component role and
   object grant.
2. On the selected object, use **Effective Access Tester**. Select the team and
   operation, then select **Run test**.

The tester returns **Allowed** or **Denied** with a reason. The **Audit Timeline**
shows recent access changes for that object.

The user must select the same team in the **Active team** selector in the page
header. Switching teams immediately replaces the visible roles and settings.

## Common access setups

| Goal | Team role | Object grant | Optional setting |
|---|---|---|---|
| Draft and manage a proposal | `proposal writer` | Read, Edit, Delete on the proposal | Donor, outcome, or field context |
| Review a proposal | `project reviewer` | Read on the proposal | Donor, outcome, or field context |
| Manage donor knowledge cards | `knowledge manager donors` | Required permissions on each card | `donor` |
| Manage outcome knowledge cards | `knowledge manager outcome` | Required permissions on each card | `outcome` |
| Manage field-context knowledge cards | `knowledge manager field context` | Required permissions on each card | `field_context` |
| Use and manage a template | `access_template` | Required permissions on the template | `donor` |
| View metrics | `access_metrics` | None | None |

## Revoke or troubleshoot access

To revoke access, remove any required gate:

- Select **Revoke** on the object grant to remove access only to that object.
- Select **Remove ROLE_NAME** under **Component Roles** to affect every member of
  the team.
- Select **Remove member** to revoke everything the user inherits from the team.

Deleting a scoped setting removes its filter and may expand access. It is not a
revocation method.

If a user cannot access an object, check this order:

1. The user has an **ACTIVE** membership.
2. The user selected the correct **Active team**.
3. The team has the required **Component Role**.
4. The team has the required object permission.
5. The user's scoped setting matches the object's donor, outcome, or field
   context.

Direct ordinary user-role assignment and direct user object grants are not
supported. Configure access through **Teams**, **Settings**, and the relevant
object tab.
