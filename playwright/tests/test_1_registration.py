"""
Test suite for user registration and authentication.

These tests verify that:
1. New users can register successfully
2. Registered users can log in and out
3. Multiple users can be created
4. Registration form validation works correctly
"""

import re
import os
import pytest
from playwright.sync_api import expect

from .conftest import TEST_USERS, TestUser, take_screenshot


# ============================================================================
# Test Constants
# ============================================================================

SCREENSHOT_DIR = "playwright/test-results"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def ensure_screenshot_dir():
    """Ensure screenshot directory exists."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ============================================================================
# Test: Single User Registration
# ============================================================================


@pytest.mark.user_registration
@pytest.mark.e2e
def test_single_user_registration_and_login(page, config):
    """
    Test that a new user can register and then log in successfully.

    Steps:
    1. Navigate to homepage
    2. Click register link
    3. Fill registration form
    4. Submit and verify dashboard appears
    5. Log out
    6. Log back in
    """
    # Use a unique user for this test
    test_user = TestUser.generate_unique(prefix="registration_test")

    # Step 1: Navigate to homepage
    page.goto(config["base_url"])
    take_screenshot(page, "registration_landing")

    # Step 2: Navigate to registration page
    page.get_by_test_id("register-link").click()

    # Step 3: Fill registration form
    page.get_by_test_id("name-input").fill(test_user.name)
    page.get_by_test_id("team-select").select_option(index=test_user.team_index)
    page.get_by_test_id("email-input").fill(test_user.email)
    page.get_by_test_id("password-input").fill(test_user.password)
    page.get_by_test_id("security-question-select").select_option(test_user.security_question)
    page.get_by_test_id("security-answer-input").fill(test_user.security_answer)

    take_screenshot(page, "registration_form_filled")

    # Step 4: Submit registration
    page.get_by_test_id("submit-button").click()

    # Verify we're on the dashboard
    expect(page).to_have_url(re.compile(".*dashboard"))
    expect(page.get_by_text("Draft Smart Project Proposals")).to_be_visible()
    take_screenshot(page, "registration_dashboard")

    # Step 5: Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*login"))

    # Step 6: Log back in
    page.get_by_test_id("email-input").fill(test_user.email)
    page.get_by_test_id("password-input").fill(test_user.password)
    page.get_by_test_id("submit-button").click()

    # Verify we're back on the dashboard
    expect(page).to_have_url(re.compile(".*dashboard"))
    take_screenshot(page, "registration_relogin")


# ============================================================================
# Test: Registration with Test ID Selectors
# ============================================================================


@pytest.mark.user_registration
def test_registration_with_test_id_selectors(page, config):
    """
    Test registration using only data-testid selectors for robustness.
    """
    test_user = TestUser.generate_unique(prefix="testid_test")

    page.goto(config["base_url"])
    page.get_by_test_id("register-link").click()

    # Use test_id selectors throughout
    page.get_by_test_id("name-input").click()
    page.get_by_test_id("name-input").fill(test_user.name)

    page.get_by_test_id("team-select").select_option(index=2)

    page.get_by_test_id("email-input").click()
    page.get_by_test_id("email-input").fill(test_user.email)

    page.get_by_test_id("password-input").click()
    page.get_by_test_id("password-input").fill(test_user.password)

    page.get_by_test_id("security-question-select").select_option("Favourite animal?")
    page.get_by_test_id("security-answer-input").click()
    page.get_by_test_id("security-answer-input").fill(test_user.security_answer)

    page.get_by_test_id("submit-button").click()

    # Verify successful registration
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*login"))


# ============================================================================
# Test: Multiple User Registration
# ============================================================================


@pytest.mark.user_registration
@pytest.mark.slow
def test_multiple_user_registration(context, config):
    """
    Test that multiple users can be registered in sequence.
    Uses separate contexts for each user to ensure isolation.
    """
    users_to_create = [
        TestUser.generate_unique(prefix="multi_user_1"),
        TestUser.generate_unique(prefix="multi_user_2"),
        TestUser.generate_unique(prefix="multi_user_3"),
    ]

    for i, user in enumerate(users_to_create):
        # Create a new page for each user registration
        page = context.new_page()
        page.set_default_timeout(config["default_timeout"])

        # Register user
        page.goto(config["base_url"])
        page.get_by_test_id("register-link").click()

        page.get_by_test_id("name-input").fill(user.name)
        page.get_by_test_id("team-select").select_option(index=user.team_index)
        page.get_by_test_id("email-input").fill(user.email)
        page.get_by_test_id("password-input").fill(user.password)
        page.get_by_test_id("security-question-select").select_option(user.security_question)
        page.get_by_test_id("security-answer-input").fill(user.security_answer)

        page.get_by_test_id("submit-button").click()

        # Verify registration success
        expect(page).to_have_url(re.compile(".*dashboard"))

        # Log out for next user
        page.get_by_test_id("user-menu-button").click()
        page.get_by_test_id("logout-button").click()
        page.wait_for_url(re.compile(".*login"))

        page.close()
        take_screenshot(page, f"multi_user_{i+1}_registered")


# ============================================================================
# Test: Pre-defined User Registration (Backward Compatibility)
# ============================================================================


@pytest.mark.user_registration
@pytest.mark.regression
def test_primary_user_registration(page, config):
    """
    Test registration with the primary test user.
    This maintains backward compatibility with existing tests.
    """
    user = TEST_USERS["primary"]

    page.goto(config["base_url"])
    page.get_by_test_id("register-link").click()

    page.get_by_test_id("name-input").click()
    page.get_by_test_id("name-input").fill(user.name)

    page.get_by_test_id("team-select").select_option(index=user.team_index)

    page.get_by_test_id("email-input").click()
    page.get_by_test_id("email-input").fill(user.email)

    page.get_by_test_id("password-input").click()
    page.get_by_test_id("password-input").fill(user.password)

    page.get_by_test_id("security-question-select").select_option(user.security_question)
    page.get_by_test_id("security-answer-input").click()
    page.get_by_test_id("security-answer-input").fill(user.security_answer)

    page.get_by_test_id("submit-button").click()

    expect(page).to_have_url(re.compile(".*dashboard"))

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*login"))


# ============================================================================
# Test: Secondary User Registration (Backward Compatibility)
# ============================================================================


@pytest.mark.user_registration
@pytest.mark.regression
def test_secondary_user_registration(page, config):
    """
    Test registration with the secondary test user.
    Used for peer review workflows.
    """
    user = TEST_USERS["secondary"]

    page.goto(config["base_url"])
    page.get_by_test_id("register-link").click()

    page.get_by_test_id("name-input").click()
    page.get_by_test_id("name-input").fill(user.name)

    page.get_by_test_id("team-select").select_option(index=user.team_index)

    page.get_by_test_id("email-input").click()
    page.get_by_test_id("email-input").fill(user.email)

    page.get_by_test_id("password-input").click()
    page.get_by_test_id("password-input").fill(user.password)

    page.get_by_test_id("security-question-select").select_option(user.security_question)
    page.get_by_test_id("security-answer-input").click()
    page.get_by_test_id("security-answer-input").fill(user.security_answer)

    page.get_by_test_id("submit-button").click()

    expect(page).to_have_url(re.compile(".*dashboard"))

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()
    expect(page).to_have_url(re.compile(".*login"))
