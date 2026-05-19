"""
Test suite for Template Management functionality.

These tests verify that:
1. Users can request new donor templates
2. Administrators can approve template requests
3. Administrators can create and manage templates
4. Template request workflows function correctly

User Stories Covered:
- Donor Template Request
- Template Management (Admin)
"""

import re
import os
import pytest
from playwright.sync_api import expect

from .conftest import TEST_USERS, take_screenshot


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def ensure_screenshot_dir():
    """Ensure screenshot directory exists."""
    os.makedirs("playwright/test-results", exist_ok=True)


@pytest.fixture
def logged_in_user(page, config):
    """Log in as the primary test user."""
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))
    return page


@pytest.fixture
def logged_in_admin(page, config):
    """Log in as an administrator user."""
    user = TEST_USERS["admin"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))
    return page


# ============================================================================
# Test: Navigate to Template Request Page
# ============================================================================


@pytest.mark.template_management
@pytest.mark.smoke
def test_navigate_to_template_request_page(logged_in_user, config):
    """
    Test that users can navigate to the template request page.

    User Story: Donor Template Request
    """
    page = logged_in_user

    # Navigate to templates section
    page.get_by_test_id("templates-tab").click()
    expect(page).to_have_url(re.compile(".*templates"))

    # Click on request new template button
    page.get_by_test_id("request-template-button").click()
    expect(page).to_have_url(re.compile(".*template-request"))

    # Verify template request form is visible
    expect(page.get_by_text("Request New Donor Template")).to_be_visible()

    take_screenshot(page, "template_request_navigation")


# ============================================================================
# Test: Submit Template Request
# ============================================================================


@pytest.mark.template_management
def test_submit_template_request(logged_in_user, config):
    """
    Test that users can submit a new template request.

    User Story: Donor Template Request
    Steps:
    1. Navigate to template request page
    2. Fill in donor name
    3. Fill in template description
    4. Upload reference documents
    5. Submit request
    6. Verify success message
    """
    page = logged_in_user

    # Navigate to template request page
    page.get_by_test_id("templates-tab").click()
    page.get_by_test_id("request-template-button").click()
    expect(page).to_have_url(re.compile(".*template-request"))

    # Fill in donor name
    page.get_by_test_id("donor-name-input").click()
    page.get_by_test_id("donor-name-input").fill("Sweden - Ministry for Foreign Affairs")

    # Fill in template description
    page.get_by_test_id("template-description-input").click()
    page.get_by_test_id("template-description-input").fill("Template for education projects targeting refugee children")

    # Upload reference documents (simulate file upload)
    # Note: In a real test, you would use page.set_input_files() with actual files
    # For this test, we'll assume the upload is handled by the UI
    page.get_by_test_id("reference-documents-upload").click()

    take_screenshot(page, "template_request_form_filled")

    # Submit the request
    page.get_by_test_id("submit-template-request-button").click()

    # Verify success message
    expect(page.get_by_text("Template request submitted successfully")).to_be_visible()

    # Verify we're redirected to templates page
    expect(page).to_have_url(re.compile(".*templates"))

    take_screenshot(page, "template_request_submitted")


# ============================================================================
# Test: View Pending Template Requests (Admin)
# ============================================================================


@pytest.mark.template_management
@pytest.mark.admin
def test_view_pending_template_requests(logged_in_admin, config):
    """
    Test that administrators can view pending template requests.

    User Story: Template Management (Admin)
    Steps:
    1. Navigate to admin templates page
    2. View pending requests
    3. Verify request details are visible
    """
    page = logged_in_admin

    # Navigate to admin templates page
    page.get_by_test_id("admin-menu-button").click()
    page.get_by_test_id("template-management-button").click()
    expect(page).to_have_url(re.compile(".*admin/templates"))

    # Switch to pending requests tab
    page.get_by_test_id("pending-requests-tab").click()

    # Verify we can see pending requests
    expect(page.get_by_text("Pending Template Requests")).to_be_visible()

    take_screenshot(page, "admin_pending_template_requests")


# ============================================================================
# Test: Approve Template Request (Admin)
# ============================================================================


@pytest.mark.template_management
@pytest.mark.admin
def test_approve_template_request(logged_in_admin, config):
    """
    Test that administrators can approve template requests.

    User Story: Template Management (Admin)
    Steps:
    1. Navigate to pending template requests
    2. Select a request
    3. Click approve button
    4. Verify success message
    5. Verify requester is notified
    """
    page = logged_in_admin

    # Navigate to admin templates page
    page.get_by_test_id("admin-menu-button").click()
    page.get_by_test_id("template-management-button").click()
    expect(page).to_have_url(re.compile(".*admin/templates"))

    # Switch to pending requests tab
    page.get_by_test_id("pending-requests-tab").click()

    # Select the first pending request
    first_request = page.get_by_test_id("template-request-card").first
    donor_name = first_request.get_by_test_id("request-donor-name").text_content()

    # Click approve button
    first_request.get_by_test_id("approve-request-button").click()

    # Verify confirmation dialog appears
    expect(page.get_by_text("Approve Template Request")).to_be_visible()

    # Confirm approval
    page.get_by_test_id("confirm-approval-button").click()

    # Verify success message
    expect(page.get_by_text("Template request approved successfully")).to_be_visible()

    # Verify notification is sent (this would be tested more thoroughly in integration tests)
    expect(page.get_by_text(f"Notification sent to requester for {donor_name}")).to_be_visible()

    take_screenshot(page, "template_request_approved")


# ============================================================================
# Test: Create New Template (Admin)
# ============================================================================


@pytest.mark.template_management
@pytest.mark.admin
def test_create_new_template(logged_in_admin, config):
    """
    Test that administrators can create new templates.

    User Story: Template Management (Admin)
    Steps:
    1. Navigate to template management
    2. Click new template button
    3. Fill in template details
    4. Define template sections
    5. Save template
    6. Verify success message
    """
    page = logged_in_admin

    # Navigate to admin templates page
    page.get_by_test_id("admin-menu-button").click()
    page.get_by_test_id("template-management-button").click()
    expect(page).to_have_url(re.compile(".*admin/templates"))

    # Click new template button
    page.get_by_test_id("new-template-button").click()
    expect(page).to_have_url(re.compile(".*template-create"))

    # Fill in template details
    page.get_by_test_id("template-name-input").fill("Education Project Template")
    page.get_by_test_id("template-donor-input").fill("Sweden - Ministry for Foreign Affairs")
    page.get_by_test_id("template-description-input").fill("Standard template for education projects")

    # Define template sections
    page.get_by_test_id("add-section-button").click()
    page.get_by_test_id("section-title-input-0").fill("Executive Summary")
    page.get_by_test_id("section-prompt-input-0").fill("Generate a comprehensive executive summary")

    page.get_by_test_id("add-section-button").click()
    page.get_by_test_id("section-title-input-1").fill("Project Rationale")
    page.get_by_test_id("section-prompt-input-1").fill("Explain the rationale and justification")

    take_screenshot(page, "new_template_form_filled")

    # Save template
    page.get_by_test_id("save-template-button").click()

    # Verify success message
    expect(page.get_by_text("Template created successfully")).to_be_visible()

    # Verify we're redirected to template list
    expect(page).to_have_url(re.compile(".*admin/templates"))

    take_screenshot(page, "template_created_successfully")


# ============================================================================
# Test: Template Request Workflow (User + Admin)
# ============================================================================


@pytest.mark.template_management
@pytest.mark.e2e
def test_complete_template_request_workflow(page, config):
    """
    Complete template request workflow from user request to admin approval.

    User Story: Donor Template Request + Template Management (Admin)
    Steps:
    1. User submits template request
    2. Admin views pending requests
    3. Admin approves request
    4. Admin creates template based on request
    5. User verifies template is available
    """
    # Step 1: User submits template request
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Navigate to template request
    page.get_by_test_id("templates-tab").click()
    page.get_by_test_id("request-template-button").click()

    # Fill and submit request
    page.get_by_test_id("donor-name-input").fill("Norway - Ministry of Foreign Affairs")
    page.get_by_test_id("template-description-input").fill("Template for humanitarian aid projects")
    page.get_by_test_id("submit-template-request-button").click()

    expect(page.get_by_text("Template request submitted successfully")).to_be_visible()

    take_screenshot(page, "workflow_user_request_submitted")

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 2: Admin approves request
    admin = TEST_USERS["admin"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(admin.email)
    page.get_by_test_id("password-input").fill(admin.password)
    page.get_by_test_id("submit-button").click()

    # Navigate to admin template management
    page.get_by_test_id("admin-menu-button").click()
    page.get_by_test_id("template-management-button").click()
    page.get_by_test_id("pending-requests-tab").click()

    # Approve the request
    first_request = page.get_by_test_id("template-request-card").first
    first_request.get_by_test_id("approve-request-button").click()
    page.get_by_test_id("confirm-approval-button").click()

    expect(page.get_by_text("Template request approved successfully")).to_be_visible()

    take_screenshot(page, "workflow_admin_approved_request")

    # Step 3: Admin creates template
    page.get_by_test_id("new-template-button").click()

    page.get_by_test_id("template-name-input").fill("Norway Humanitarian Aid Template")
    page.get_by_test_id("template-donor-input").fill("Norway - Ministry of Foreign Affairs")
    page.get_by_test_id("template-description-input").fill("Standard template for Norway humanitarian projects")

    # Add sections
    page.get_by_test_id("add-section-button").click()
    page.get_by_test_id("section-title-input-0").fill("Project Overview")
    page.get_by_test_id("section-prompt-input-0").fill("Generate project overview")

    page.get_by_test_id("save-template-button").click()
    expect(page.get_by_text("Template created successfully")).to_be_visible()

    take_screenshot(page, "workflow_admin_created_template")

    # Log out admin
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 4: User verifies template is available
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # Navigate to templates
    page.get_by_test_id("templates-tab").click()

    # Verify the new template is available
    expect(page.get_by_text("Norway Humanitarian Aid Template")).to_be_visible()

    take_screenshot(page, "workflow_user_verifies_template")


# ============================================================================
# Test: Template Request Validation
# ============================================================================


@pytest.mark.template_management
def test_template_request_validation(logged_in_user, config):
    """
    Test template request form validation.

    User Story: Donor Template Request
    Steps:
    1. Try to submit empty form
    2. Verify validation errors
    3. Try to submit with missing required fields
    4. Verify appropriate error messages
    """
    page = logged_in_user

    # Navigate to template request page
    page.get_by_test_id("templates-tab").click()
    page.get_by_test_id("request-template-button").click()

    # Try to submit empty form
    page.get_by_test_id("submit-template-request-button").click()

    # Verify validation errors
    expect(page.get_by_text("Donor name is required")).to_be_visible()
    expect(page.get_by_text("Template description is required")).to_be_visible()

    take_screenshot(page, "template_request_validation_errors")

    # Fill only donor name and try to submit
    page.get_by_test_id("donor-name-input").fill("Test Donor")
    page.get_by_test_id("submit-template-request-button").click()

    # Verify description is still required
    expect(page.get_by_text("Template description is required")).to_be_visible()
    expect(page.get_by_text("Donor name is required")).not_to_be_visible()


# ============================================================================
# Test: Template Access Control
# ============================================================================


@pytest.mark.template_management
@pytest.mark.security
def test_template_access_control(page, config):
    """
    Test that template management requires appropriate permissions.

    User Story: Template Management (Admin)
    Steps:
    1. Try to access admin template management as regular user
    2. Verify access is denied
    """
    # Log in as regular user
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # Try to access admin template management directly
    page.goto(f"{config['base_url']}/admin/templates")

    # Verify access is denied
    expect(page.get_by_text("Access Denied")).to_be_visible()
    expect(page.get_by_text("You do not have permission to access this page")).to_be_visible()

    take_screenshot(page, "template_access_control_denied")
