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

from .conftest import take_screenshot


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
    page.get_by_role("button", name="Request Elevated Access").click()
    page.locator("select").nth(1).select_option("5")
    page.get_by_role("button", name="Submit Request").click()
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("settings-button").click()
    page.locator(".settings-select > .css-13cymwt-control > .css-hlgwow > .css-19bb58m").first.click()
    page.get_by_role("option", name="Canada", exact=True).click()
    page.get_by_role("button", name="Save Changes").click()

    take_screenshot(page, "profile_page_navigation")


# ============================================================================
# Test: Update User Role and Settings Information
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

    # Request Roles
    page.get_by_role("button", name="Request Elevated Access").click()
    page.locator("select").nth(1).select_option("5")
    take_screenshot(page, "profile_request_role")
    page.get_by_role("button", name="Submit Request").click()
    page.get_by_test_id("user-menu-button").click()

    # Adjust preferences
    page.get_by_test_id("settings-button").click()
    page.locator(".settings-select > .css-13cymwt-control > .css-hlgwow > .css-19bb58m").first.click()
    page.get_by_role("option", name="Canada", exact=True).click()
    take_screenshot(page, "profile_settings")
    page.get_by_role("button", name="Save Changes").click()

    # Verify success message
    expect(page.get_by_text("Profile updated successfully")).to_be_visible()

    # Verify updated information is displayed
    expect(page.get_by_test_id("name-input")).to_have_value("John Smith Updated")
    expect(page.get_by_test_id("geographic-coverage-input")).to_have_value("Africa, Middle East")

    take_screenshot(page, "profile_update_success")


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
    page.goto(f"{config['base_url']}/dashboard")

    # Verify we're redirected to login page
    expect(page).to_have_url(re.compile(".*login"))

    take_screenshot(page, "profile_access_control_unauthenticated")
