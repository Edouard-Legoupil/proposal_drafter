"""
Test suite for User Profile Management functionality.

These tests verify that:
1. Users can update their role
2. Users can change their settings
3. Profile updates are persisted correctly

User Stories Covered:
- Update user profile
- Change password
"""

import re
import pytest
from playwright.sync_api import expect

from .conftest import TEST_USERS, take_screenshot


# ========================================================================================================================================================
# Test: Navigate to Profile Page
# ============================================================================


@pytest.mark.user_profile
@pytest.mark.smoke
def test_navigate_to_profile_page(logged_in_page, config):
    """
    Test that users can navigate to their profile page.

    User Story: Update user profile
    """
    page = logged_in_page

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
def test_update_user_profile_information(logged_in_page, config):
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
    page = logged_in_page

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
# Test: Profile Information Persistence
# ============================================================================


@pytest.mark.user_profile
def test_profile_information_persistence(logged_in_page, config):
    """
    Test that profile information persists after page refresh.

    User Story: Update user profile
    Steps:
    1. Update profile information
    2. Refresh the page
    3. Verify information is still present
    """
    page = logged_in_page

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
def test_full_profile_management_workflow(logged_in_page, config):
    """
    Complete profile management workflow.

    User Story: Update user profile
    Steps:
    1. Navigate to profile
    2. Update profile information
    3. Log out and log back in
    4. Verify profile information persists
    """
    page = logged_in_page

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

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*login"))

    # Log back in with original password
    page.get_by_test_id("email-input").fill(TEST_USERS["primary"].email)
    page.get_by_test_id("password-input").fill(TEST_USERS["primary"].password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Verify profile information persists
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("profile-button").click()
    expect(page.get_by_test_id("name-input")).to_have_value("Full Test User")
    expect(page.get_by_test_id("geographic-coverage-input")).to_have_value("Global")

    take_screenshot(page, "full_workflow_completed")
