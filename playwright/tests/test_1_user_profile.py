"""
Test suite for User Profile Management functionality.

These tests verify that:
1. Users can update their profile information
2. Users can change their password
3. Profile updates are persisted correctly

User Stories Covered:
- Update user profile
- Change password
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


# ============================================================================
# Test: Navigate to Profile Page
# ============================================================================


@pytest.mark.user_profile
@pytest.mark.smoke
def test_navigate_to_profile_page(logged_in_user, config):
    """
    Test that users can navigate to their profile page.

    User Story: Update user profile
    """
    page = logged_in_user

    # Open user menu
    page.get_by_test_id("user-menu-button").click()

    # Click on profile option
    page.get_by_test_id("profile-button").click()

    # Verify we're on the profile page
    expect(page).to_have_url(re.compile(".*profile"))
    expect(page.get_by_text("User Profile")).to_be_visible()

    take_screenshot(page, "profile_page_navigation")


# ============================================================================
# Test: Update User Profile Information
# ============================================================================


@pytest.mark.user_profile
def test_update_user_profile_information(logged_in_user, config):
    """
    Test that users can update their profile information.

    User Story: Update user profile
    Steps:
    1. Navigate to profile page
    2. Update name field
    3. Update geographic coverage
    4. Save changes
    5. Verify success message
    6. Verify updated information is displayed
    """
    page = logged_in_user

    # Navigate to profile page
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("profile-button").click()
    expect(page).to_have_url(re.compile(".*profile"))

    # Update name
    page.get_by_test_id("name-input").click()
    page.get_by_test_id("name-input").fill("John Smith Updated")

    # Update geographic coverage
    page.get_by_test_id("geographic-coverage-input").click()
    page.get_by_test_id("geographic-coverage-input").fill("Africa, Middle East")

    take_screenshot(page, "profile_update_form_filled")

    # Save changes
    page.get_by_test_id("save-profile-button").click()

    # Verify success message
    expect(page.get_by_text("Profile updated successfully")).to_be_visible()

    # Verify updated information is displayed
    expect(page.get_by_test_id("name-input")).to_have_value("John Smith Updated")
    expect(page.get_by_test_id("geographic-coverage-input")).to_have_value("Africa, Middle East")

    take_screenshot(page, "profile_update_success")


# ============================================================================
# Test: Change Password
# ============================================================================


@pytest.mark.user_profile
def test_change_password(logged_in_user, config):
    """
    Test that users can change their password.

    User Story: Change password
    Steps:
    1. Navigate to profile page
    2. Enter current password
    3. Enter new password
    4. Confirm new password
    5. Submit change
    6. Verify success message
    """
    page = logged_in_user

    # Navigate to profile page
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("profile-button").click()
    expect(page).to_have_url(re.compile(".*profile"))

    # Click on change password section or button
    page.get_by_test_id("change-password-button").click()

    # Enter current password
    page.get_by_test_id("current-password-input").click()
    page.get_by_test_id("current-password-input").fill(TEST_USERS["primary"].password)

    # Enter new password
    new_password = "newpassword123"
    page.get_by_test_id("new-password-input").click()
    page.get_by_test_id("new-password-input").fill(new_password)

    # Confirm new password
    page.get_by_test_id("confirm-password-input").click()
    page.get_by_test_id("confirm-password-input").fill(new_password)

    take_screenshot(page, "password_change_form_filled")

    # Submit password change
    page.get_by_test_id("change-password-submit-button").click()

    # Verify success message
    expect(page.get_by_text("Password changed successfully")).to_be_visible()

    take_screenshot(page, "password_change_success")


# ============================================================================
# Test: Password Change Validation
# ============================================================================


@pytest.mark.user_profile
def test_password_change_validation(logged_in_user, config):
    """
    Test password change validation.

    User Story: Change password
    Steps:
    1. Navigate to profile page
    2. Try to change password with mismatched confirmation
    3. Verify error message
    4. Try to change password with weak password
    5. Verify error message
    """
    page = logged_in_user

    # Navigate to profile page
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("profile-button").click()
    expect(page).to_have_url(re.compile(".*profile"))

    # Click on change password section or button
    page.get_by_test_id("change-password-button").click()

    # Test mismatched password confirmation
    page.get_by_test_id("current-password-input").fill(TEST_USERS["primary"].password)
    page.get_by_test_id("new-password-input").fill("newpassword123")
    page.get_by_test_id("confirm-password-input").fill("differentpassword123")

    page.get_by_test_id("change-password-submit-button").click()

    # Verify error message for mismatched passwords
    expect(page.get_by_text("Passwords do not match")).to_be_visible()

    take_screenshot(page, "password_validation_mismatch")

    # Clear fields
    page.get_by_test_id("new-password-input").clear()
    page.get_by_test_id("confirm-password-input").clear()

    # Test weak password validation
    page.get_by_test_id("new-password-input").fill("weak")
    page.get_by_test_id("confirm-password-input").fill("weak")

    page.get_by_test_id("change-password-submit-button").click()

    # Verify error message for weak password
    expect(page.get_by_text("Password must be at least 8 characters")).to_be_visible()

    take_screenshot(page, "password_validation_weak")


# ============================================================================
# Test: Profile Information Persistence
# ============================================================================


@pytest.mark.user_profile
def test_profile_information_persistence(logged_in_user, config):
    """
    Test that profile information persists after page refresh.

    User Story: Update user profile
    Steps:
    1. Update profile information
    2. Refresh the page
    3. Verify information is still present
    """
    page = logged_in_user

    # Navigate to profile page
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("profile-button").click()
    expect(page).to_have_url(re.compile(".*profile"))

    # Update profile information
    page.get_by_test_id("name-input").click()
    page.get_by_test_id("name-input").fill("Jane Doe Test")

    page.get_by_test_id("save-profile-button").click()
    expect(page.get_by_text("Profile updated successfully")).to_be_visible()

    # Refresh the page
    page.reload()

    # Verify information persists
    expect(page.get_by_test_id("name-input")).to_have_value("Jane Doe Test")

    take_screenshot(page, "profile_persistence_after_refresh")


# ============================================================================
# Test: Profile Page Access Control
# ============================================================================


@pytest.mark.user_profile
@pytest.mark.security
def test_profile_page_access_control(page, config):
    """
    Test that profile page requires authentication.

    User Story: Update user profile
    Steps:
    1. Try to access profile page without login
    2. Verify redirection to login page
    """
    # Try to access profile page directly
    page.goto(f"{config['base_url']}/profile")

    # Verify we're redirected to login page
    expect(page).to_have_url(re.compile(".*login"))

    take_screenshot(page, "profile_access_control_unauthenticated")


# ============================================================================
# Test: Full Profile Management Workflow
# ============================================================================


@pytest.mark.user_profile
@pytest.mark.e2e
def test_full_profile_management_workflow(logged_in_user, config):
    """
    Complete profile management workflow.

    User Story: Update user profile + Change password
    Steps:
    1. Navigate to profile
    2. Update profile information
    3. Change password
    4. Log out and log back in with new password
    5. Verify profile information persists
    """
    page = logged_in_user

    # Navigate to profile page
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("profile-button").click()
    expect(page).to_have_url(re.compile(".*profile"))

    # Update profile information
    page.get_by_test_id("name-input").click()
    page.get_by_test_id("name-input").fill("Full Test User")
    page.get_by_test_id("geographic-coverage-input").click()
    page.get_by_test_id("geographic-coverage-input").fill("Global")

    page.get_by_test_id("save-profile-button").click()
    expect(page.get_by_text("Profile updated successfully")).to_be_visible()

    take_screenshot(page, "full_workflow_profile_updated")

    # Change password
    page.get_by_test_id("change-password-button").click()
    page.get_by_test_id("current-password-input").fill(TEST_USERS["primary"].password)
    new_password = "testpassword123"
    page.get_by_test_id("new-password-input").fill(new_password)
    page.get_by_test_id("confirm-password-input").fill(new_password)

    page.get_by_test_id("change-password-submit-button").click()
    expect(page.get_by_text("Password changed successfully")).to_be_visible()

    take_screenshot(page, "full_workflow_password_changed")

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*login"))

    # Log back in with new password
    page.get_by_test_id("email-input").fill(TEST_USERS["primary"].email)
    page.get_by_test_id("password-input").fill(new_password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Verify profile information persists
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("profile-button").click()
    expect(page.get_by_test_id("name-input")).to_have_value("Full Test User")
    expect(page.get_by_test_id("geographic-coverage-input")).to_have_value("Global")

    take_screenshot(page, "full_workflow_completed")
