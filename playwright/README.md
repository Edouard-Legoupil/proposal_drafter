# Playwright End-to-End Testing


This directory contains the end-to-end test suite for the Proposal Drafter application frontend using [Playwright](https://playwright.dev/).


## User Stories and Test Suite Overview

The test suite covers the complete user journey

### User Profile Management

**Feature:** User Profile Management
**Description:** Users should be able to manage their profile information

```gherkin
Feature: User Profile Management
  As a logged-in user
  I want to manage my profile information
  So that my account information is up-to-date

  Scenario: Update user profile
    Given I am logged in
    And I am on my profile page
    When I update my name to "John Smith"
    And I update my geographic coverage to "Africa"
    And I click the "Save" button
    Then I should see a success message "Profile updated successfully"
    And my profile should show the updated information

```

 **test_1_user_profile.py** - User registration, login, and profile management

### Proposal


**Feature:** Proposal Creation
**Description:** Users should be able to create new project proposals

```gherkin
Feature: Proposal Creation
  As a logged-in user
  I want to create new project proposals
  So that I can develop funding applications for my projects

  Scenario: Create a new proposal
    Given I am logged in
    And I am on the dashboard
    When I click the "New Proposal" button
    Then I should be redirected to the proposal creation page
    And I should see the proposal form with required fields

  Scenario: Fill and submit proposal form
    Given I am on the proposal creation page
    When I enter the project short name "Refugee Children Education Initiative"
    And I enter the project description "Establishing a comprehensive primary education program for 2,500 refugee children aged 6-14"
    And I select the main outcomes "OA11. Education" and "OA7. Community Engagement"
    And I enter the beneficiaries profile "2,500 refugee children aged 6-14"
    And I enter the potential implementing partners "UNHCR, UNICEF, Save the Children"
    And I select the geographical scope "One Country Operation"
    And I select the country "Afghanistan"
    And I select the budget range "1M$"
    And I select the duration "12 months"
    And I select the targeted donor "Sweden - Ministry for Foreign Affairs"
    And I click the "Generate" button
    Then the system should generate the proposal sections
    And I should see the generated proposal with editable sections

  Scenario: Save proposal as draft
    Given I have created a proposal
    When I click the "Save Draft" button
    Then the proposal should be saved with status "draft"
    And I should see a confirmation message "Proposal saved as draft"
```


**Feature:** Proposal Editing
**Description:** Users should be able to edit existing proposals

```gherkin
Feature: Proposal Editing
  As a proposal owner
  I want to edit my proposals
  So that I can refine and improve the content

  Scenario: Edit a proposal section
    Given I am viewing my proposal
    When I click the "Edit" button for the "Executive Summary" section
    Then the section should become editable
    And I should see save and cancel buttons

  Scenario: Save edited section
    Given I am editing a proposal section
    When I make changes to the content
    And I click the "Save" button
    Then the changes should be saved
    And the section should return to read-only mode
    And I should see a success message "Section updated successfully"

  Scenario: Cancel editing
    Given I am editing a proposal section
    When I click the "Cancel" button
    Then the section should revert to its original content
    And return to read-only mode
```


**Feature:** Section Regeneration
**Description:** Users should be able to regenerate proposal sections with new instructions

```gherkin
Feature: Section Regeneration
  As a proposal owner
  I want to regenerate proposal sections
  So that I can improve the content based on specific requirements

  Scenario: Regenerate a section with new instructions
    Given I am viewing my proposal
    When I click the "Regenerate" button for a section
    Then I should see a dialog with a prompt input field

  Scenario: Submit regeneration request
    Given I have opened the regeneration dialog for a section
    When I enter specific instructions "Revise this section to fit in 200 characters"
    And I click the "Regenerate" button
    Then the system should regenerate the section content
    And I should see the updated section with the new content
    And I should see a success message "Section regenerated successfully"
```


**Feature:** Proposal Status Management
**Description:** Users should be able to manage the status of their proposals

```gherkin
Feature: Proposal Status Management
  As a proposal owner
  I want to manage the status of my proposals
  So that I can track their progress through the workflow

  Scenario: Submit proposal for review
    Given I have a completed proposal
    When I click the "Submit for Review" button
    Then the proposal status should change to "review"
    And I should see a confirmation message "Proposal submitted for review"

  Scenario: Mark proposal as validated
    Given I have a reviewed proposal
    When I click the "Mark as Validated" button
    Then the proposal status should change to "validated"
    And I should see a confirmation message "Proposal marked as validated"

  Scenario: Archive completed proposal
    Given I have a validated proposal
    When I click the "Archive" button
    Then the proposal status should change to "archived"
    And I should see a confirmation message "Proposal archived"
```

 **test_2_proposal_creation.py** - Complete proposal creation workflow


### Knowledge Card


**Feature:** Knowledge Card Creation
**Description:** Users should be able to create knowledge cards to capture project insights

```gherkin
Feature: Knowledge Card Creation
  As a logged-in user
  I want to create knowledge cards
  So that I can capture and share project insights and lessons learned

  Scenario: Create a new knowledge card
    Given I am logged in
    And I am on the dashboard
    When I click the "New Knowledge Card" button
    Then I should be redirected to the knowledge card creation page
    And I should see the knowledge card form

  Scenario: Fill and submit knowledge card form
    Given I am on the knowledge card creation page
    When I enter the title "Education Program Lessons"
    And I enter the description "Key insights from implementing education programs in refugee camps"
    And I select the relevant outcomes
    And I add relevant tags
    And I upload supporting documents
    And I click the "Save" button
    Then the knowledge card should be created
    And I should see a success message "Knowledge card created successfully"
```


**Feature:** Knowledge Card Review
**Description:** Users should be able to review and provide feedback on knowledge cards

```gherkin
Feature: Knowledge Card Review
  As a reviewer
  I want to review knowledge cards
  So that I can ensure quality and relevance of shared knowledge

  Scenario: Submit a review for a knowledge card
    Given I am viewing a knowledge card
    When I click the "Add Review" button
    Then I should see a review form

  Scenario: Submit review feedback
    Given I have opened the review form for a knowledge card
    When I enter my review comments
    And I select a rating
    And I click the "Submit Review" button
    Then the review should be saved
    And I should see a success message "Review submitted successfully"
    And the knowledge card should show the review status as "pending"
```


. **test_3_knowledge_card_new.py** - Knowledge card creation and management


### Peer Review

**Feature:** Peer Review
**Description:** Users should be able to request and conduct peer reviews of proposals

```gherkin
Feature: Peer Review
  As a proposal owner
  I want to request peer reviews
  So that I can get feedback from colleagues before final submission

  Scenario: Request a peer review
    Given I have a proposal ready for review
    When I click the "Request Peer Review" button
    And I select a reviewer from the list
    And I enter review instructions
    And I click the "Send Request" button
    Then the review request should be sent
    And the reviewer should receive a notification
    And I should see a success message "Peer review requested"

  Scenario: Conduct a peer review
    Given I am a reviewer
    And I have received a peer review request
    When I open the proposal for review
    And I add review comments
    And I select the review status
    And I click the "Submit Review" button
    Then the review should be saved
    And the proposal owner should be notified
```

 **test_4_peer_review_new.py** - Proposal peer review functionality

### Dashboard

**Feature:** Dashboard Navigation
**Description:** Users should be able to navigate the dashboard

```gherkin
Feature: Dashboard Navigation
  As a logged-in user
  I want to navigate the dashboard
  So that I can access different features

  Scenario: Navigate to different sections
    Given I am logged in
    When I click on the "Proposals" tab
    Then I should be redirected to the proposals page
    And I should see a list of my proposals

    When I click on the "Knowledge Cards" tab
    Then I should be redirected to the knowledge cards page
    And I should see a list of knowledge cards

    When I click on the "Reports" tab
    Then I should be redirected to the reports page
    And I should see a list of available reports

    When I click on the "Users" tab
    Then I should be redirected to the users page
    And I should see a list of users

    When I click on the "Settings" tab
    Then I should be redirected to the settings page
    And I should see the settings options
```

 **test_5_dashboard.py** - Dashboard navigation and features

### Template

**Feature:** Template Management
**Description:** Administrators should be able to manage donor templates

```gherkin
Feature: Template Management
  As an administrator
  I want to manage donor templates
  So that I can ensure users have access to appropriate templates

  Scenario: Approve a template request
    Given I am an administrator
    And I am viewing pending template requests
    When I click the "Approve" button for a template request
    Then the template should be approved
    And the requester should be notified

  Scenario: Create a new template
    Given I am an administrator
    And I am on the template management page
    When I click the "New Template" button
    And I fill in the template details
    And I define the template sections
    And I click the "Save" button
    Then the new template should be created
    And I should see a success message "Template created successfully"
```

 **test_6_template_management.py** - Template management workflows

### Incident Management

**Feature:** Incident Management
**Description:** The system should log and manage incidents

```gherkin
Feature: Incident Management
  As a system administrator
  I want to manage system incidents
  So that I can track and resolve issues

  Scenario: View system incidents
    Given I am an administrator
    And I am on the incident management page
    When I filter incidents by type
    Then I should see a list of incidents matching the filter
    And each incident should show details and status

  Scenario: Resolve an incident
    Given I am viewing an incident
    When I click the "Mark as Resolved" button
    And I enter resolution notes
    And I click the "Save" button
    Then the incident status should change to "resolved"
    And I should see a success message "Incident resolved"
```

**test_7_quality_gate_review.py** - Quality gate and review processes

### Administration

**Feature:** User Access Management
**Description:** Administrators should be able to manage user access and roles

```gherkin
Feature: User Access Management
  As an administrator
  I want to manage user access and roles
  So that I can control system permissions

  Scenario: Grant user access to a resource
    Given I am an administrator
    And I am on the access management page
    When I select a user
    And I select a resource type
    And I select the specific resource
    And I select the access level
    And I click the "Grant Access" button
    Then the user should be granted access
    And I should see a success message "Access granted successfully"

  Scenario: Revoke user access
    Given I am an administrator
    And I am viewing a user's access permissions
    When I click the "Revoke Access" button for a specific permission
    Then the user's access should be revoked
    And I should see a success message "Access revoked successfully"
```


**Feature:** System Configuration
**Description:** Administrators should be able to configure system settings

```gherkin
Feature: System Configuration
  As an administrator
  I want to configure system settings
  So that I can customize the system for our organization

  Scenario: Configure system parameters
    Given I am an administrator
    And I am on the system configuration page
    When I update the maximum proposal size
    And I update the default template
    And I click the "Save Configuration" button
    Then the configuration should be saved
    And I should see a success message "Configuration updated successfully"
```


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



```gherkin
Feature: Role request

  Scenario: Submit role request
    Given user requests role
    Then admin can approve or reject
```


```gherkin
Feature: Object access explorer

  Scenario: View access matrix
    Given object selected
    Then show all users and reasons for access
```


```gherkin
Feature: User access explorer

  Scenario: View full access
    Given user selected
    Then show all accessible artifacts
```


```gherkin
Feature: Audit logs

  Scenario: Track permission changes
    Given roles updated
    Then audit log captures change
```


```gherkin
Feature: Bulk updates

  Scenario: Assign roles in bulk
    Given multiple users selected
    When apply role
    Then all users updated
```

```gherkin
Feature: User deactivation

  Scenario: Reassign artifacts
    Given user owns artifacts
    When deactivated
    Then ownership must be reassigned
```


```gherkin
Feature: Permission Simulation

  Scenario: Preview access
    Given unsaved changes
    When simulate
    Then show resulting permissions
```



```gherkin
Feature: Admin Dashboard

  Scenario: View summary
    Then show users, incidents, and requests
```


```gherkin
Feature: Security for Admin Dashboard

  Scenario: Prevent unauthorized access
    Given user lacks access
    Then API returns 403
```


**test_8_admin.py** - System configuration and user management


## Test Execution

#### Prerequisites
- Node.js v18+
- Python 3.10+
- Playwright installed (`npm install -g @playwright/test`)
- Backend server running (`cd backend && uvicorn main:app --host 0.0.0.0 --port 8502`)
- Frontend server running (`cd frontend && npm run dev`)

After installing the Python packages, install the browser binaries:

```bash
playwright install
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install
```

For headless Linux environments (CI/CD servers):

```bash
playwright install-deps

```

#### Running Tests

```bash

source backend/venv/bin/activate
# Run all tests
pytest playwright/tests/ -v

# Run specific test file
pytest playwright/tests/test_1_user_profile.py

# Run in headed mode (show browser)
pytest playwright/tests/ --headed -v

# Run with trace viewing
pytest playwright/tests/ --trace on -v

# Show test report
pytest playwright/tests/ --report
```

### Test Data Management

The test suite includes a preparation script to set up test data:

```bash
# Prepare test data (creates test users, roles, etc.)
pytest playwright/tests/prep_1_registration.py
```

### Best Practices

1. **Test Isolation**: Each test should clean up after itself
2. **Data Setup**: Use the preparation scripts for consistent test data
3. **Error Handling**: Tests include proper error handling and retries
4. **Screenshots**: Tests capture screenshots on failure for debugging
5. **Traces**: Full execution traces are available for debugging


### Test Maintenance

When adding new features:
1. Create a new test file following the naming convention `test_N_feature_name.py`
2. Follow the existing test patterns and page object models
3. Add the test to the comprehensive suite if it's a core workflow
4. Update this README with the new test file information

### Troubleshooting

**Common Issues:**
- **Database state**: Run preparation scripts to reset test data
- **Browser issues**: Reinstall Playwright browsers with `npx playwright install`
- **Test flakiness**: Use `npx playwright test --retries=2` for flaky tests



## 🔧 Test Development

### Page Object Model

The tests use a Page Object Model pattern for maintainability. Key page objects include:
- `LoginPage`
- `DashboardPage`
- `ProposalCreationPage`
- `KnowledgeCardPage`
- `AdminPanel`


### Fixtures

The test suite uses pytest fixtures for better maintainability:

- `config`: Session-scoped configuration with environment variable support
- `playwright`: Session-scoped Playwright instance
- `browser`: Session-scoped browser instance
- `context`: Function-scoped browser context with video recording
- `page`: Function-scoped page instance
- `logged_in_page`: Page with pre-authenticated user
- `registered_user`: Creates and returns a new registered user
- `TestUser`: Class for managing test user credentials
- `TEST_USERS`: Predefined test users dictionary




### Test Marks

Tests are categorized using pytest marks:

- `@pytest.mark.smoke` - Quick sanity checks
- `@pytest.mark.e2e` - End-to-end user journeys
- `@pytest.mark.regression` - Regression tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.user_registration` - User registration tests
- `@pytest.mark.proposal_creation` - Proposal creation tests
- `@pytest.mark.knowledge_card` - Knowledge card tests
- `@pytest.mark.peer_review` - Peer review tests
- `@pytest.mark.dashboard` - Dashboard tests

### Screenshots and Videos

Screenshots are automatically saved to `playwright/test-results/screenshots/` with descriptive names.

Video recordings are saved to `playwright/test-results/videos/` when enabled. Each test that uses the `context` fixture with video recording enabled will generate a video file.

### Recording User Journeys with Codegen Tool

You can use Playwright's codegen tool to record new test interactions:

```bash
python3 -m playwright codegen http://localhost:8502 --test-id-attribute data-testid
```

The frontend uses `data-testid` attributes for robust element selection. The codegen tool will:

- Record page navigation as `page.goto('url')`
- Record clicks as `page.click('selector')`
- Record text input as `page.fill('selector', 'text')`

After recording, copy the generated Python script into the appropriate test file and refactor as needed to use the fixtures and follow the test patterns.

### Best Practices

1. **Use fixtures**: Prefer using fixtures (`page`, `config`, `logged_in_page`) over manual setup
2. **Use test IDs**: Always use `data-testid` selectors when available
3. **Add assertions**: Use `expect()` to verify UI state
4. **Handle timeouts**: Use appropriate timeouts for long operations (generation can take minutes)
5. **Clean up**: Tests should clean up after themselves when possible
6. **Mark tests**: Use appropriate pytest marks for categorization
7. **Skip when needed**: Use `pytest.skip()` when preconditions aren't met
8. **Document**: Add docstrings explaining test purpose and preconditions
