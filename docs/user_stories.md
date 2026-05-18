# Proposal Drafter - User Stories Documentation

## Table of Contents

1. [User Profile Management](#user-profile-management)
2. [Proposal Creation and Management](#proposal-creation-and-management)
3. [Knowledge Management](#knowledge-management)
4. [Template Management](#template-management)
5. [Review and Collaboration](#review-and-collaboration)
6. [Document Export and Sharing](#document-export-and-sharing)
7. [Administrative Functions](#administrative-functions)
8. [System Monitoring and Health](#system-monitoring-and-health)

---



## User Profile Management

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

  Scenario: Change password
    Given I am logged in
    And I am on my profile page
    When I enter my current password "password123"
    And I enter a new password "newpassword123"
    And I confirm the new password "newpassword123"
    And I click the "Change Password" button
    Then I should see a success message "Password changed successfully"
```

---

## Proposal Creation and Management

### Proposal Creation

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

### Proposal Editing

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

### Section Regeneration

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

### Proposal Status Management

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

---

## Knowledge Management

### Knowledge Card Creation

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

### Knowledge Card Review

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

---

## Template Management

### Donor Template Request

**Feature:** Donor Template Request
**Description:** Users should be able to request new donor templates

```gherkin
Feature: Donor Template Request
  As a logged-in user
  I want to request new donor templates
  So that I can have templates tailored to specific donor requirements

  Scenario: Request a new donor template
    Given I am logged in
    And I am on the dashboard
    When I click the "Request Donor Template" button
    Then I should be redirected to the template request page

  Scenario: Submit template request
    Given I am on the template request page
    When I enter the donor name "Sweden - Ministry for Foreign Affairs"
    And I enter the template description "Template for education projects"
    And I upload reference documents
    And I click the "Submit Request" button
    Then the template request should be created
    And I should see a success message "Template request submitted successfully"
```

### Template Management (Admin)

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

---

## Review and Collaboration

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

### Quality Gate Review

**Feature:** Quality Gate Review
**Description:** Quality assurance team should be able to conduct quality gate reviews

```gherkin
Feature: Quality Gate Review
  As a quality assurance officer
  I want to conduct quality gate reviews
  So that I can ensure proposals meet organizational standards

  Scenario: Conduct a quality gate review
    Given I am a QA officer
    And I am viewing a proposal for quality review
    When I check the proposal against quality criteria
    And I add quality review comments
    And I select the quality status
    And I click the "Submit Quality Review" button
    Then the quality review should be saved
    And the proposal owner should be notified of the result
```

---

## Document Export and Sharing

### Document Export

**Feature:** Document Export
**Description:** Users should be able to export proposals in various formats

```gherkin
Feature: Document Export
  As a proposal owner
  I want to export my proposals
  So that I can share them with donors and stakeholders

  Scenario: Export proposal to Word
    Given I am viewing my proposal
    When I click the "Export to Word" button
    Then the system should generate a Word document
    And the document should download automatically
    And I should see a success message "Proposal exported to Word"

  Scenario: Export proposal to Excel
    Given I am viewing my proposal
    When I click the "Export to Excel" button
    Then the system should generate an Excel spreadsheet
    And the spreadsheet should download automatically
    And I should see a success message "Proposal exported to Excel"

  Scenario: Export proposal to PDF
    Given I am viewing my proposal
    When I click the "Export to PDF" button
    Then the system should generate a PDF document
    And the PDF should download automatically
    And I should see a success message "Proposal exported to PDF"
```

### Document Sharing

**Feature:** Document Sharing
**Description:** Users should be able to share proposals with colleagues

```gherkin
Feature: Document Sharing
  As a proposal owner
  I want to share my proposals with colleagues
  So that they can review or collaborate on the proposal

  Scenario: Share proposal with a colleague
    Given I am viewing my proposal
    When I click the "Share" button
    And I enter the colleague's email
    And I select the access level
    And I click the "Share" button
    Then the colleague should receive access to the proposal
    And I should see a success message "Proposal shared successfully"
```

---

## Administrative Functions

### User Access Management

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

### System Configuration

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

---

## System Monitoring and Health

### Health Check

**Feature:** Health Check
**Description:** The system should provide health monitoring endpoints

```gherkin
Feature: Health Check
  As a system administrator
  I want to monitor system health
  So that I can ensure the system is running properly

  Scenario: Check system health
    Given the system is running
    When I send a GET request to the health endpoint
    Then I should receive a JSON response with status "ok"
    And the response should include system metrics

  Scenario: Check database connectivity
    Given the system is running
    When I send a GET request to the database health endpoint
    Then I should receive a response indicating database status
    And if the database is healthy, the status should be "healthy"
```

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

---
