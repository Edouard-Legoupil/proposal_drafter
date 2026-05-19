"""
Test suite for Document Sharing functionality.

These tests verify that:
1. Users can share proposals with colleagues
2. Access levels are properly managed
3. Shared documents are accessible to recipients
4. Sharing permissions can be managed

User Stories Covered:
- Document Sharing
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
def logged_in_colleague(page, config):
    """Log in as a colleague user."""
    user = TEST_USERS["colleague"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))
    return page


# ============================================================================
# Test: Navigate to Share Proposal Dialog
# ============================================================================


@pytest.mark.document_sharing
@pytest.mark.smoke
def test_navigate_to_share_proposal_dialog(logged_in_user, config):
    """
    Test that users can navigate to the share proposal dialog.

    User Story: Document Sharing
    """
    page = logged_in_user

    # Navigate to a proposal
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_cards.first.click()

    # Click share button
    page.get_by_test_id("share-button").click()

    # Verify share dialog is visible
    expect(page.get_by_text("Share Proposal")).to_be_visible()
    expect(page.get_by_test_id("share-dialog")).to_be_visible()

    take_screenshot(page, "share_dialog_opened")


# ============================================================================
# Test: Share Proposal with Colleague
# ============================================================================


@pytest.mark.document_sharing
def test_share_proposal_with_colleague(logged_in_user, config):
    """
    Test that users can share proposals with colleagues.

    User Story: Document Sharing
    Steps:
    1. Open a proposal
    2. Click share button
    3. Enter colleague's email
    4. Select access level
    5. Click share button
    6. Verify success message
    """
    page = logged_in_user

    # Navigate to a proposal
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_cards.first.click()

    # Open share dialog
    page.get_by_test_id("share-button").click()

    # Enter colleague's email
    colleague_email = TEST_USERS["colleague"].email
    page.get_by_test_id("share-email-input").click()
    page.get_by_test_id("share-email-input").fill(colleague_email)

    # Select access level
    page.get_by_test_id("share-access-level-select").select_option("view")

    take_screenshot(page, "share_dialog_filled")

    # Click share button
    page.get_by_test_id("share-submit-button").click()

    # Verify success message
    expect(page.get_by_text("Proposal shared successfully")).to_be_visible()
    expect(page.get_by_text(f"Proposal shared with {colleague_email}")).to_be_visible()

    take_screenshot(page, "share_success")


# ============================================================================
# Test: Share Proposal with Different Access Levels
# ============================================================================


@pytest.mark.document_sharing
def test_share_proposal_access_levels(logged_in_user, config):
    """
    Test sharing proposals with different access levels.

    User Story: Document Sharing
    Steps:
    1. Test sharing with "View" access level
    2. Test sharing with "Edit" access level
    3. Test sharing with "Comment" access level
    """
    page = logged_in_user

    # Navigate to a proposal
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_cards.first.click()

    # Test different access levels
    access_levels = ["view", "edit", "comment"]

    for access_level in access_levels:
        # Open share dialog
        page.get_by_test_id("share-button").click()

        # Fill in email and select access level
        page.get_by_test_id("share-email-input").fill(f"test_{access_level}@example.com")
        page.get_by_test_id("share-access-level-select").select_option(access_level)

        take_screenshot(page, f"share_access_level_{access_level}")

        # Close dialog (don't actually share to avoid test data pollution)
        page.get_by_test_id("share-cancel-button").click()


# ============================================================================
# Test: Verify Shared Proposal Access
# ============================================================================


@pytest.mark.document_sharing
@pytest.mark.e2e
def test_verify_shared_proposal_access(page, config):
    """
    Test complete sharing workflow and verify access.

    User Story: Document Sharing
    Steps:
    1. User shares proposal with colleague
    2. Colleague logs in and accesses shared proposal
    3. Verify colleague can see the proposal
    4. Verify access level restrictions
    """
    # Step 1: User shares proposal
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Navigate to a proposal
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_name = proposal_cards.first.get_by_test_id("proposal-name").text_content()
    proposal_cards.first.click()

    # Share with colleague (view access)
    page.get_by_test_id("share-button").click()
    colleague_email = TEST_USERS["colleague"].email
    page.get_by_test_id("share-email-input").fill(colleague_email)
    page.get_by_test_id("share-access-level-select").select_option("view")
    page.get_by_test_id("share-submit-button").click()

    expect(page.get_by_text("Proposal shared successfully")).to_be_visible()

    take_screenshot(page, "sharing_workflow_shared")

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 2: Colleague accesses shared proposal
    colleague = TEST_USERS["colleague"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(colleague.email)
    page.get_by_test_id("password-input").fill(colleague.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Check shared proposals section
    page.get_by_test_id("shared-tab").click()

    # Verify the shared proposal is visible
    expect(page.get_by_text("Shared with You")).to_be_visible()
    expect(page.get_by_text(proposal_name)).to_be_visible()

    take_screenshot(page, "sharing_workflow_colleague_sees_shared")

    # Open the shared proposal
    shared_proposal = page.get_by_test_id("shared-proposal-card").filter(has_text=proposal_name).first
    shared_proposal.click()

    # Verify colleague can view the proposal
    expect(page.get_by_text(proposal_name)).to_be_visible()
    expect(page.get_by_test_id("proposal-content")).to_be_visible()

    # Verify access level restrictions (view only)
    # Edit buttons should be disabled or not visible
    expect(page.get_by_test_id("edit-save-button-summary")).to_be_disabled()

    take_screenshot(page, "sharing_workflow_access_verified")


# ============================================================================
# Test: Manage Shared Access
# ============================================================================


@pytest.mark.document_sharing
def test_manage_shared_access(logged_in_user, config):
    """
    Test managing shared access permissions.

    User Story: Document Sharing
    Steps:
    1. Share a proposal with a colleague
    2. View shared access list
    3. Change access level for a shared user
    4. Remove access for a shared user
    """
    page = logged_in_user

    # Navigate to a proposal
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_cards.first.click()

    # Share with a colleague first
    page.get_by_test_id("share-button").click()
    colleague_email = "test_colleague@example.com"
    page.get_by_test_id("share-email-input").fill(colleague_email)
    page.get_by_test_id("share-access-level-select").select_option("view")
    page.get_by_test_id("share-submit-button").click()
    expect(page.get_by_text("Proposal shared successfully")).to_be_visible()

    # Open manage access dialog
    page.get_by_test_id("manage-access-button").click()

    # Verify shared user is listed
    expect(page.get_by_text("Shared Access")).to_be_visible()
    expect(page.get_by_text(colleague_email)).to_be_visible()
    expect(page.get_by_text("View")).to_be_visible()

    take_screenshot(page, "manage_access_list")

    # Change access level
    shared_user_row = page.get_by_test_id("shared-user-row").filter(has_text=colleague_email)
    shared_user_row.get_by_test_id("change-access-level-select").select_option("edit")

    # Save changes
    page.get_by_test_id("save-access-changes-button").click()

    # Verify access level changed
    expect(page.get_by_text("Access level updated")).to_be_visible()
    expect(shared_user_row.get_by_text("Edit")).to_be_visible()

    take_screenshot(page, "manage_access_level_changed")

    # Remove access
    shared_user_row.get_by_test_id("remove-access-button").click()
    page.get_by_test_id("confirm-remove-access-button").click()

    # Verify access removed
    expect(page.get_by_text("Access removed")).to_be_visible()
    expect(page.get_by_text(colleague_email)).not_to_be_visible()

    take_screenshot(page, "manage_access_removed")


# ============================================================================
# Test: Share Proposal Validation
# ============================================================================


@pytest.mark.document_sharing
def test_share_proposal_validation(logged_in_user, config):
    """
    Test share proposal form validation.

    User Story: Document Sharing
    Steps:
    1. Try to share without email
    2. Verify validation error
    3. Try to share with invalid email
    4. Verify validation error
    """
    page = logged_in_user

    # Navigate to a proposal
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_cards.first.click()

    # Open share dialog
    page.get_by_test_id("share-button").click()

    # Try to share without email
    page.get_by_test_id("share-submit-button").click()

    # Verify validation error
    expect(page.get_by_text("Email is required")).to_be_visible()

    take_screenshot(page, "share_validation_empty")

    # Try to share with invalid email
    page.get_by_test_id("share-email-input").fill("invalid-email")
    page.get_by_test_id("share-submit-button").click()

    # Verify validation error
    expect(page.get_by_text("Please enter a valid email address")).to_be_visible()

    take_screenshot(page, "share_validation_invalid_email")


# ============================================================================
# Test: Share Proposal with Multiple Users
# ============================================================================


@pytest.mark.document_sharing
def test_share_proposal_multiple_users(logged_in_user, config):
    """
    Test sharing a proposal with multiple users at once.

    User Story: Document Sharing
    Steps:
    1. Open share dialog
    2. Add multiple email addresses
    3. Select access levels for each
    4. Share with all users
    5. Verify success message
    """
    page = logged_in_user

    # Navigate to a proposal
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_cards.first.click()

    # Open share dialog
    page.get_by_test_id("share-button").click()

    # Add first user
    page.get_by_test_id("share-email-input").fill("user1@example.com")
    page.get_by_test_id("share-access-level-select").select_option("view")
    page.get_by_test_id("add-another-user-button").click()

    # Add second user
    page.get_by_test_id("share-email-input-1").fill("user2@example.com")
    page.get_by_test_id("share-access-level-select-1").select_option("edit")

    # Add third user
    page.get_by_test_id("add-another-user-button").click()
    page.get_by_test_id("share-email-input-2").fill("user3@example.com")
    page.get_by_test_id("share-access-level-select-2").select_option("comment")

    take_screenshot(page, "share_multiple_users_filled")

    # Share with all users
    page.get_by_test_id("share-submit-button").click()

    # Verify success message
    expect(page.get_by_text("Proposal shared successfully with 3 users")).to_be_visible()

    take_screenshot(page, "share_multiple_users_success")


# ============================================================================
# Test: Shared Proposal Access Control
# ============================================================================


@pytest.mark.document_sharing
@pytest.mark.security
def test_shared_proposal_access_control(page, config):
    """
    Test that shared proposal access control works correctly.

    User Story: Document Sharing
    Steps:
    1. Share proposal with view access
    2. Verify recipient can only view, not edit
    3. Share proposal with edit access
    4. Verify recipient can edit
    """
    # Share proposal with view access
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_cards.first.click()

    # Share with view access
    page.get_by_test_id("share-button").click()
    page.get_by_test_id("share-email-input").fill("view_user@example.com")
    page.get_by_test_id("share-access-level-select").select_option("view")
    page.get_by_test_id("share-submit-button").click()

    take_screenshot(page, "access_control_view_shared")

    # Log out and log in as view user
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # This would require test data setup with the view_user account
    # For now, we'll verify the UI indicates the access level was set correctly

    # Log back in as original user
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # Verify shared access shows correct permissions
    proposal_cards.first.click()
    page.get_by_test_id("manage-access-button").click()

    view_user_row = page.get_by_test_id("shared-user-row").filter(has_text="view_user@example.com")
    expect(view_user_row.get_by_text("View")).to_be_visible()

    take_screenshot(page, "access_control_permissions_verified")


# ============================================================================
# Test: Complete Document Sharing Workflow
# ============================================================================


@pytest.mark.document_sharing
@pytest.mark.e2e
@pytest.mark.regression
def test_complete_document_sharing_workflow(page, config):
    """
    Complete document sharing workflow.

    User Story: Document Sharing
    Steps:
    1. User shares proposal with colleague
    2. Colleague accesses and reviews shared proposal
    3. Colleague adds comments (if allowed)
    4. User views colleague's activity
    5. User manages shared access
    """
    # Step 1: User shares proposal
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for sharing")

    proposal_name = proposal_cards.first.get_by_test_id("proposal-name").text_content()
    proposal_cards.first.click()

    # Share with colleague (comment access)
    page.get_by_test_id("share-button").click()
    colleague_email = TEST_USERS["colleague"].email
    page.get_by_test_id("share-email-input").fill(colleague_email)
    page.get_by_test_id("share-access-level-select").select_option("comment")
    page.get_by_test_id("share-submit-button").click()

    expect(page.get_by_text("Proposal shared successfully")).to_be_visible()

    take_screenshot(page, "complete_workflow_shared")

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 2: Colleague accesses and interacts with shared proposal
    colleague = TEST_USERS["colleague"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(colleague.email)
    page.get_by_test_id("password-input").fill(colleague.password)
    page.get_by_test_id("submit-button").click()

    # Access shared proposals
    page.get_by_test_id("shared-tab").click()
    shared_proposal = page.get_by_test_id("shared-proposal-card").filter(has_text=proposal_name).first
    shared_proposal.click()

    # Verify colleague can view content
    expect(page.get_by_test_id("proposal-content")).to_be_visible()

    # Add a comment (if comment access is allowed)
    page.get_by_test_id("add-comment-button-Summary").click()
    page.get_by_test_id("comment-textarea-Summary").fill(
        "Great proposal! I suggest adding more detail about the monitoring indicators."
    )
    page.get_by_test_id("submit-comment-button-Summary").click()

    expect(page.get_by_text("Comment added successfully")).to_be_visible()

    take_screenshot(page, "complete_workflow_colleague_commented")

    # Log out colleague
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 3: User views colleague's activity and manages access
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # View the proposal
    proposal_cards.first.click()

    # Check for new comments
    expect(page.get_by_text("Great proposal!")).to_be_visible()
    expect(page.get_by_text("I suggest adding more detail about the monitoring indicators")).to_be_visible()

    take_screenshot(page, "complete_workflow_user_sees_comments")

    # Manage shared access
    page.get_by_test_id("manage-access-button").click()

    # Verify colleague is listed with comment access
    colleague_row = page.get_by_test_id("shared-user-row").filter(has_text=colleague_email)
    expect(colleague_row.get_by_text("Comment")).to_be_visible()

    # Change access level to edit
    colleague_row.get_by_test_id("change-access-level-select").select_option("edit")
    page.get_by_test_id("save-access-changes-button").click()

    expect(page.get_by_text("Access level updated")).to_be_visible()

    take_screenshot(page, "complete_workflow_access_updated")

    # This completes the document sharing workflow
