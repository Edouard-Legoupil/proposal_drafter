# Admin Access Control User Journeys

This document contains all user journeys and Gherkin user stories for configuring user-, role-, and object-based access
across proposals, knowledge cards, templates, metrics, and incidents.

---

## Role assignment

```gherkin
Feature: Role assignment

  Background:
    Given I am authenticated as a system admin

  Scenario: Assign proposal reviewer role
    Given I open the Users section
    When I add a new user with required attributes
    And I assign role "proposal reviewer" and select the linked relevant outcomes, field context or donors he is allowed to review
    Then the user gets restricted access

  Scenario: Remove a role
    Given a user has "project reviewer"
    When I remove it
    Then access to review features is revoked

  Scenario: Assign knowledge manager donor role
    When I assign "knowledge manager donors" role with donor groups
    Then access is granted only for those donor-scoped knowledge cards
```


---

## 3. Team Management

```gherkin
Feature: Team management

  Scenario: Assign user to team
    Given a user exists
    When I assign them to a team
    Then proposal access aligns with team membership
```

---

## 4. Access Dimensions (Donor, Outcome, Field Context)

```gherkin
Feature: Access dimensions

  Scenario: Assign donor groups
    Given a user exists
    When I assign donor groups
    Then access expands according to role compatibility
```

---

## 5. Proposal Access

```gherkin
Feature: Proposal access

  Scenario: Transfer ownership
    Given a proposal exists
    When I assign a new owner
    Then ownership updates and access recalculates

  Scenario: Assign reviewer
    Given a user has reviewer role
    When assigned to proposal
    Then they can review
```

---

## 6. Knowledge Card Access

```gherkin
Feature: Knowledge card access

  Scenario: Donor manager edits card
    Given user has donor manager role
    When card belongs to donor
    Then user can edit
```

---

## 7. Template Access

```gherkin
Feature: Template access

  Scenario: Approve template request
    Given request exists
    When admin approves
    Then template becomes usable
```

---

## 8. Metrics Access

```gherkin
Feature: Metrics access

  Scenario: Filter metrics
    Given non-admin user
    When viewing metrics
    Then only accessible data is shown
```

---

## 9. Incident Access

```gherkin
Feature: Incident access

  Scenario: Access linked incident
    Given user has access to source artifact
    Then user can access incident
```

---

## 10. Access Requests

```gherkin
Feature: Role request

  Scenario: Submit role request
    Given user requests role
    Then admin can approve or reject
```

---

## 11. Object Access Explorer

```gherkin
Feature: Object access explorer

  Scenario: View access matrix
    Given object selected
    Then show all users and reasons for access
```

---

## 12. User Access Explorer

```gherkin
Feature: User access explorer

  Scenario: View full access
    Given user selected
    Then show all accessible artifacts
```

---

## 13. Audit Logging

```gherkin
Feature: Audit logs

  Scenario: Track permission changes
    Given roles updated
    Then audit log captures change
```

---

## 14. Bulk Operations

```gherkin
Feature: Bulk updates

  Scenario: Assign roles in bulk
    Given multiple users selected
    When apply role
    Then all users updated
```

---

## 15. Deprovisioning

```gherkin
Feature: User deactivation

  Scenario: Reassign artifacts
    Given user owns artifacts
    When deactivated
    Then ownership must be reassigned
```

---

## 16. Permission Simulation

```gherkin
Feature: Simulation

  Scenario: Preview access
    Given unsaved changes
    When simulate
    Then show resulting permissions
```

---

## 17. Admin Dashboard

```gherkin
Feature: Dashboard

  Scenario: View summary
    Then show users, incidents, and requests
```

---

## Security Guarantees

```gherkin
Feature: Security

  Scenario: Prevent unauthorized access
    Given user lacks access
    Then API returns 403
```

-
