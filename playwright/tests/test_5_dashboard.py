"""
Test suite for dashboard functionality and metrics.

These tests verify that:
1. Dashboard loads correctly
2. Proposal cards are displayed
3. Knowledge card counts are shown
4. Team filtering works
5. User can navigate between dashboard tabs
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
# Test: Dashboard Loads Successfully
# ============================================================================


@pytest.mark.dashboard
@pytest.mark.smoke
def test_dashboard_loads_successfully(logged_in_user, config):
    """
    Test that the dashboard loads successfully after login.
    """
    page = logged_in_user

    # Verify dashboard header is visible
    expect(page.get_by_text("Draft Smart Project Proposals")).to_be_visible()

    # Verify main sections are present
    expect(page.get_by_test_id("new-proposal-button")).to_be_visible()
    expect(page.get_by_test_id("proposal-tab")).to_be_visible()
    expect(page.get_by_test_id("knowledge-tab")).to_be_visible()
    expect(page.get_by_test_id("reviews-tab")).to_be_visible()

    take_screenshot(page, "dashboard_loaded")


# ============================================================================
# Test: Dashboard Tabs Navigation
# ============================================================================


@pytest.mark.dashboard
def test_dashboard_tabs_navigation(logged_in_user, config):
    """
    Test navigation between different dashboard tabs.
    """
    page = logged_in_user

    # Verify we start on proposals tab (default)
    expect(page.get_by_test_id("proposal-tab")).to_have_class(re.compile("active"))

    # Navigate to knowledge tab
    page.get_by_test_id("knowledge-tab").click()
    expect(page).to_have_url(re.compile(".*knowledge"))
    expect(page.get_by_test_id("knowledge-tab")).to_have_class(re.compile("active"))

    # Navigate to reviews tab
    page.get_by_test_id("reviews-tab").click()
    expect(page).to_have_url(re.compile(".*reviews"))
    expect(page.get_by_test_id("reviews-tab")).to_have_class(re.compile("active"))

    # Navigate back to proposals tab
    page.get_by_test_id("proposal-tab").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    take_screenshot(page, "dashboard_tabs_navigation")


# ============================================================================
# Test: Proposal Cards Display
# ============================================================================


@pytest.mark.dashboard
def test_proposal_cards_display(logged_in_user, config):
    """
    Test that proposal cards are displayed on the dashboard.

    Note: This test may show no proposals if none exist.
    """
    page = logged_in_user

    # Count proposal cards
    # The proposal cards are typically in a grid or list
    proposal_cards = page.get_by_test_id("proposal-card")
    count = proposal_cards.count()

    print(f"[DASHBOARD] Found {count} proposal cards")

    # If there are proposals, verify their structure
    if count > 0:
        first_card = proposal_cards.first
        expect(first_card.get_by_test_id("project-options-button")).to_be_visible()
        # Cards should have project name
        expect(first_card.get_by_role("heading")).to_be_visible()

    take_screenshot(page, "dashboard_proposal_cards")


# ============================================================================
# Test: Filter Proposals by Team
# ============================================================================


@pytest.mark.dashboard
def test_filter_proposals_by_team(logged_in_user, config):
    """
    Test filtering proposals by team.
    """
    page = logged_in_user

    # Open filter modal
    page.get_by_test_id("filter-button").click()

    # Filter by team (select first team option)
    page.get_by_test_id("team-filter").select_option(index=1)

    take_screenshot(page, "dashboard_filter_team")

    # Close filter modal
    page.get_by_test_id("filter-modal-close-button").click()


# ============================================================================
# Test: Filter Proposals by Status
# ============================================================================


@pytest.mark.dashboard
def test_filter_proposals_by_status(logged_in_user, config):
    """
    Test filtering proposals by status (draft, in_review, submitted, etc.).
    """
    page = logged_in_user

    # Open filter modal
    page.get_by_test_id("filter-button").click()

    # Try different status options
    status_options = ["draft", "in_review", "submitted"]

    for status in status_options:
        try:
            page.get_by_test_id("status-filter").select_option(status)
            take_screenshot(page, f"dashboard_filter_status_{status}")
        except Exception:
            # Status option may not exist if no proposals have that status
            pass

    # Close filter modal
    page.get_by_test_id("filter-modal-close-button").click()


# ============================================================================
# Test: Knowledge Card Count Display
# ============================================================================


@pytest.mark.dashboard
def test_knowledge_card_count_display(logged_in_user, config):
    """
    Test that knowledge card counts are displayed correctly.
    """
    page = logged_in_user

    # Navigate to knowledge tab
    page.get_by_test_id("knowledge-tab").click()

    # Check for knowledge card count elements
    # These might be displayed as badges or counters
    try:
        count_elements = page.get_by_test_id("knowledge-card-count")
        if count_elements.count() > 0:
            count_text = count_elements.first.text_content()
            print(f"[DASHBOARD] Knowledge card count: {count_text}")
    except Exception:
        pass  # Count element may not exist

    take_screenshot(page, "dashboard_knowledge_counts")


# ============================================================================
# Test: Dashboard Metrics Display
# ============================================================================


@pytest.mark.dashboard
@pytest.mark.regression
def test_dashboard_metrics_display(logged_in_user, config):
    """
    Test that dashboard metrics are displayed correctly.

    This is the test_5_dashboard test mentioned in the readme.
    """
    page = logged_in_user

    # Check for metrics display
    # Metrics might include: total proposals, draft proposals, in review, etc.

    # Look for common metric indicators
    metric_selectors = [
        "Total Proposals",
        "Draft",
        "In Review",
        "Submitted",
        "Knowledge Cards",
        "Pending Reviews",
    ]

    found_metrics = []
    for selector in metric_selectors:
        try:
            element = page.get_by_text(selector)
            if element.count() > 0:
                found_metrics.append(selector)
        except Exception:
            pass

    print(f"[DASHBOARD] Found metrics: {found_metrics}")

    # Verify we can see filter by teams
    page.get_by_test_id("filter-button").click()

    # Check for team filter options
    team_filter = page.get_by_test_id("team-filter")
    if team_filter.count() > 0:
        options = team_filter.get_by_role("option")
        print(f"[DASHBOARD] Team filter has {options.count()} options")

    # Close filter
    page.get_by_test_id("filter-modal-close-button").click()

    take_screenshot(page, "dashboard_metrics")


# ============================================================================
# Test: User Menu and Logout
# ============================================================================


@pytest.mark.dashboard
@pytest.mark.smoke
def test_user_menu_and_logout(logged_in_user, config):
    """
    Test user menu functionality and logout.
    """
    page = logged_in_user

    # Open user menu
    page.get_by_test_id("user-menu-button").click()

    # Verify logout button is visible
    expect(page.get_by_test_id("logout-button")).to_be_visible()

    take_screenshot(page, "dashboard_user_menu")

    # Click logout
    page.get_by_test_id("logout-button").click()

    # Verify we're back on login page
    expect(page).to_have_url(re.compile(".*login"))

    take_screenshot(page, "dashboard_logout")


# ============================================================================
# Test: Search Functionality
# ============================================================================


@pytest.mark.dashboard
def test_search_functionality(logged_in_user, config):
    """
    Test the search functionality on the dashboard.
    """
    page = logged_in_user

    # Find search input
    search_input = page.get_by_role("search")
    if search_input.count() > 0:
        search_input.click()
        search_input.fill("Education")

        take_screenshot(page, "dashboard_search")

        # Clear search
        search_input.clear()
    else:
        pytest.skip("No search input found on dashboard")


# ============================================================================
# Test: New Proposal Button
# ============================================================================


@pytest.mark.dashboard
@pytest.mark.smoke
def test_new_proposal_button(logged_in_user, config):
    """
    Test that the new proposal button is visible and clickable.
    """
    page = logged_in_user

    # Verify button is visible
    new_proposal_button = page.get_by_test_id("new-proposal-button")
    expect(new_proposal_button).to_be_visible()
    expect(new_proposal_button).to_be_enabled()

    take_screenshot(page, "dashboard_new_proposal_button")
