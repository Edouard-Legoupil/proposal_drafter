# Access Management System Specification

## 1. Overview

The system implements multi-dimensional access control based on:

1. Team Membership
2. Role Assignment (per team)
3. Component-level Authorization (via roles)
4. Settings-based filtering (within components)

---

## 2. Core Concepts

### 2.1 Users
- Authenticated entity
- Can belong to one or more teams

---

### 2.2 Teams
- Logical grouping of users
- Created only by System Administrators

---

### 2.3 Roles
- Roles map to React components - except 2 specific roles: system_admin and team_leader
- Roles are static and hardcoded

Example:
```
VIEW_DASHBOARD -> DashboardPage
```

---

### 2.4 Team-Scoped Roles
- Roles are assigned to teams
- Users inherit roles via team membership

---

### 2.5 Special Role: TEAM_LEADER

The system defines a specific role: `TEAM_LEADER`.

#### Capabilities:
- Approve membership requests
- Reject membership requests
- View pending requests

#### Constraint:
- Applies only within the assigned team

---

### 2.6 Settings
- Fine-grained filters applied within components - used to filter data within components (based on donors, field_context or outcomees), Depending on the componnent, the settings either filter the data displayed in the component, or restrict the ability to edit.

---

## 3. Minim target Data Model

### User
```
{id, email, name}
```

### Team
```
{id, name, description, created_by, created_at}
```

### Membership
```
{user_id, team_id, status, joined_at}
```

### Role
```
{role_key, component}
```

### TeamRoleAssignment
```
{team_id, role_key}
```

### Settings
```
{id, user_id, team_id, role_key, key, value}
```

---

## 4. Functional Requirements

### Authentication
- Required for all endpoints

---

### Team Management
- Only System Admin can create teams and assign roles to teams.

---

### Membership Workflow

#### User
- Request to join → PENDING

#### TEAM_LEADER / Admin
- Approve → ACTIVE
- Reject → REJECTED

---

### Authorization Rules

Access is granted if:
```
User ∈ Team AND Team has Role
```

---

### Settings Enforcement

Process:
1. Check role
2. Load settings
3. Apply filters (either view or edit, depending on the component)

---

### Frontend Rules
- Hide components without role - including in the sidebar and menu items
- Load roles on login or team switch

---

## 5. API Endpoints

### Teams
- POST /teams
- GET /teams

### Membership
- POST /teams/{id}/join
- GET /teams/{id}/requests
- POST /teams/{id}/approve/{user_id}

### Roles
- GET /roles
- POST /teams/{id}/roles

### Settings
- GET /settings
- POST /settings

---

## 6. Security
- Backend enforces all authorization
- Frontend is not trusted

---

## 7. Checklist

### Backend
- Membership validation
- Role validation
- Settings applied

### Frontend
- Role-based rendering

---

## 8. Principles
- Least privilege
- Clear separation: Roles vs Settings

### Implemented authorization contract

- The current team is explicit session context and can be changed only to an
  active membership. Switching replaces the role and setting context; roles
  from multiple teams are never unioned.
- Static component roles are assigned to teams by `role_key`. Runtime role
  creation and direct ordinary user-role assignment are unsupported.
- `SYSTEM_ADMIN` is the sole global bypass. `TEAM_LEADER` is member-scoped and
  permits request decisions only in the assigned active team.
- Settings use the full `(user_id, team_id, role_key, key)` scope and load only
  after component-role authorization.
- Object grants are team-only and use the normalized permissions `read`,
  `edit`, and `delete`. Ownership alone and legacy direct-user grants do not
  grant ordinary access.
- Existing installations migrate with
  `db/migrations/20260727_access_management_compliance.sql`; ambiguous legacy
  assignments are recorded in a migration report instead of broadening access.

---


## 9. Admin Interface Requirements

The system must expose a dedicated **Admin Interface** allowing full management of the access control system.

### 9.1 Scope of Admin Interface

The admin interface must enable:

- Team lifecycle management
- Membership approval workflows
- Role assignment to teams
- Settings configuration
- Object-level access control

---

### 9.2 Team & Membership Management

Admin users must be able to:
- Create, update, delete teams
- Assign or remove users from teams
- Approve/reject membership requests
- Assign TEAM_LEADER role

---

### 9.3 Role Management UI

- Display all available roles (derived from React components)
- Assign/unassign roles to a team
- Clearly indicate component mapping

---

### 9.4 Settings Management

- View and modify settings per:
  - User
  - Team
  - Role
- Provide UI controls for filtering rules (key/value pairs)

---

### 9.5 Object-Level Access Control

In addition to component-level roles, the admin interface must support **object-level permissions** scoped by team.

#### Supported Objects:
- Proposals
- Knowledge Cards
- Templates

#### Requirements:

Each object must include:
```
{
  id,
  team_id,
  created_by,
  access_rules
}
```

#### Access Rules

Access rules define which teams can:
- Read
- Edit
- Delete

Example:
```
{
  "team_id": "team-A",
  "permissions": ["read", "edit"]
}
```

---

### 9.6 Object Access Logic

Access to an object is granted if:

```
User ∈ Team
AND Team has required role
AND Team has object permission
```

---

### 9.7 Enforcement (Backend)

Every object-related endpoint must enforce:

1. Team membership validation
2. Role validation
3. Object-level permission validation

---

### 9.8 Frontend Behavior

- Objects must be filtered based on team access
- Editing controls visible only if permitted
- Creation tied to active team context

---

### 9.9 Admin UX Considerations

- Central dashboard for permissions overview
- Matrix view (Teams × Roles × Objects)
- Search and filtering capabilities
- Clear separation between:
  - Component access (roles)
  - Data access (object-level)

---
