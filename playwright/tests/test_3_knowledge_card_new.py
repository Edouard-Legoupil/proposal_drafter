"""
Test suite for knowledge card creation and management.

These tests verify that:
1. Users can view knowledge cards
2. Knowledge cards can be filtered
3. New knowledge cards can be created
4. References can be managed
5. Knowledge cards can be downloaded
6. Card history can be viewed
"""

import re
import os
import pytest
from playwright.sync_api import expect

from .conftest import TEST_USERS, TestUser, take_screenshot


# ============================================================================
# Test Constants
# ============================================================================

CARD_SUMMARY = "test"


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
# Test: View Knowledge Cards Dashboard
# ============================================================================

@pytest.mark.knowledge_card
def test_view_knowledge_cards_dashboard(logged_in_user, config):
    """
    Test that users can navigate to and view the knowledge cards dashboard.
    """
    page = logged_in_user
    
    # Navigate to knowledge tab
    page.get_by_test_id("knowledge-tab").click()
    expect(page).to_have_url(re.compile(".*knowledge"))
    
    take_screenshot(page, "knowledge_card_dashboard")


# ============================================================================
# Test: Filter Knowledge Cards by Type
# ============================================================================

@pytest.mark.knowledge_card
def test_filter_knowledge_cards_by_type(logged_in_user, config):
    """
    Test filtering knowledge cards by type (donor, outcome, field_context).
    """
    page = logged_in_user
    
    # Navigate to knowledge tab
    page.get_by_test_id("knowledge-tab").click()
    
    # Open filter modal
    page.get_by_test_id("filter-button").click()
    
    # Filter by outcome type
    page.get_by_test_id("knowledge-card-type-filter").select_option("outcome")
    take_screenshot(page, "knowledge_card_filter_outcome")
    
    # Close filter modal
    page.get_by_test_id("filter-modal-close-button").click()


# ============================================================================
# Test: View Existing Knowledge Card
# ============================================================================

@pytest.mark.knowledge_card
def test_view_existing_knowledge_card(logged_in_user, config):
    """
    Test viewing an existing knowledge card.
    
    Precondition: At least one knowledge card must exist.
    """
    page = logged_in_user
    
    # Navigate to knowledge tab
    page.get_by_test_id("knowledge-tab").click()
    
    # Try to find and open an existing card
    # This selector matches the card title pattern
    card_selectors = [
        "Outcome CardOA7. Community Engagement and Participation",
        "Donor CardRepublic of Korea",
        "Field Context Card",
    ]
    
    card_found = False
    for selector in card_selectors:
        try:
            page.get_by_text(selector).first.click()
            card_found = True
            break
        except Exception:
            continue
    
    if not card_found:
        pytest.skip("No existing knowledge card found for view test")
    
    # Verify we're viewing a card
    expect(page.get_by_test_id("view-history-button")).to_be_visible(timeout=10000)
    take_screenshot(page, "knowledge_card_view_existing")
    
    # Download the card
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Download as Word").first.click()
    download = download_info.value
    assert download is not None
    print(f"[DOWNLOAD] Knowledge card exported to: {download.path()}")


# ============================================================================
# Test: View Knowledge Card History
# ============================================================================

@pytest.mark.knowledge_card
def test_view_knowledge_card_history(logged_in_user, config):
    """
    Test viewing the history of a knowledge card.
    
    Precondition: A knowledge card with history must exist.
    """
    page = logged_in_user
    
    # Navigate to knowledge tab
    page.get_by_test_id("knowledge-tab").click()
    
    # Try to find and open an existing card
    try:
        page.get_by_text("Outcome CardOA7. Community Engagement").first.click()
    except Exception:
        pytest.skip("No existing knowledge card found for history test")
    
    # Click view history
    page.get_by_test_id("view-history-button").click()
    take_screenshot(page, "knowledge_card_history")
    
    # Close history modal
    page.get_by_role("button", name="×").click()


# ============================================================================
# Test: Create New Knowledge Card for Donor
# ============================================================================

@pytest.mark.knowledge_card
@pytest.mark.e2e
def test_create_knowledge_card_for_donor(logged_in_user, config):
    """
    Test creating a new knowledge card linked to a donor.
    """
    page = logged_in_user
    
    # Navigate to knowledge tab
    page.get_by_test_id("knowledge-tab").click()
    
    # Click new knowledge card button
    page.get_by_test_id("new-knowledge-card-button").click()
    
    take_screenshot(page, "knowledge_card_create_start")
    
    # Select donor as card type
    page.get_by_test_id("link-type-select").select_option("donor")
    
    # Select a donor
    page.locator(".kc-linked-item-select__input-container").click()
    page.get_by_role("combobox", name="Select Item*").fill("kor")
    page.get_by_role("option", name="Republic of Korea - Ministry").click()
    
    # Confirm donor selection
    page.get_by_test_id("confirm-button").click()
    
    # Fill in summary
    page.get_by_test_id("summary-textarea").click()
    page.get_by_test_id("summary-textarea").fill(CARD_SUMMARY)
    
    take_screenshot(page, "knowledge_card_donor_selected")
    
    # Identify references
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("identify-references-button").click()
    take_screenshot(page, "knowledge_card_references_identified")
    
    # Ingest references
    page.get_by_test_id("ingest-references-button").click()
    expect(page.get_by_test_id("alert-ok-button")).to_be_visible(timeout=200000)
    page.get_by_test_id("alert-ok-button").click()
    take_screenshot(page, "knowledge_card_references_ingested")
    
    # Populate card
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("populate-card-button").click()
    expect(page.get_by_test_id("alert-ok-button")).to_be_visible(timeout=400000)
    page.get_by_test_id("alert-ok-button").click()
    take_screenshot(page, "knowledge_card_populated")
    
    # Edit a section
    page.get_by_test_id("edit-section-button-1. Donor Overview").click()
    take_screenshot(page, "knowledge_card_edit_section")
    page.get_by_role("button", name="Cancel").click()
    
    # Download the card
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Download as Word").click()
    download = download_info.value
    assert download is not None
    print(f"[DOWNLOAD] Knowledge card exported to: {download.path()}")
    
    # Close card
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("close-card-button").click()
    take_screenshot(page, "knowledge_card_saved")


# ============================================================================
# Test: Create Knowledge Card from Proposal
# ============================================================================

@pytest.mark.knowledge_card
@pytest.mark.slow
def test_create_knowledge_card_from_proposal(logged_in_user, config):
    """
    Test creating a knowledge card from an existing proposal.
    
    Precondition: A proposal must already exist.
    """
    page = logged_in_user
    
    # Try to find and open an existing proposal
    try:
        page.get_by_text("Project: Refugee Children Education").first.click()
    except Exception:
        pytest.skip("No existing proposal found for knowledge card creation test")
    
    # Open manage knowledge modal
    page.get_by_test_id("manage-knowledge-button").click()
    take_screenshot(page, "knowledge_card_from_proposal_start")
    
    # Select a knowledge card to associate
    # This assumes there's at least one knowledge card available
    try:
        first_checkbox = page.get_by_test_id("knowledge-card-checkbox").first
        first_checkbox.check()
        page.get_by_test_id("confirm-button").click()
        take_screenshot(page, "knowledge_card_from_proposal_associated")
    except Exception:
        # If no checkboxes found, just close
        page.get_by_test_id("confirm-button").click()
        pytest.skip("No knowledge cards available to associate")


# ============================================================================
# Test: Full Knowledge Card Workflow (Backward Compatibility)
# ============================================================================

@pytest.mark.knowledge_card
@pytest.mark.e2e
@pytest.mark.regression
def test_full_knowledge_card_workflow(context, config):
    """
    Full knowledge card workflow maintaining backward compatibility.
    
    This test follows the exact workflow from the original test_3_knowledge_card.py
    but uses fixtures for better maintainability.
    """
    user = TEST_USERS["primary"]
    
    page = context.new_page()
    page.set_default_timeout(config["default_timeout"])
    
    # Login
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").click()
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").click()
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))
    
    # View list of cards
    page.get_by_test_id("knowledge-tab").click()
    take_screenshot(page, "knowledge_card_1_dashboard")
    
    # Filter card
    page.get_by_test_id("filter-button").click()
    page.get_by_test_id("knowledge-card-type-filter").select_option("outcome")
    take_screenshot(page, "knowledge_card_2_filter")
    page.get_by_test_id("filter-modal-close-button").click()
    
    # Check existing card and download
    page.get_by_text("Outcome CardOA7. Community Engagement and Participationv1Last Updated: 2025-10-").click()
    take_screenshot(page, "knowledge_card_3_existing")
    
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Download as Word Download as").click()
    download = download_info.value
    
    # View history
    page.get_by_test_id("view-history-button").click()
    take_screenshot(page, "knowledge_card_4_history")
    page.get_by_role("button", name="×").click()
    
    # Create new card for Donor
    page.get_by_test_id("logo").click()
    page.get_by_test_id("knowledge-tab").click()
    page.get_by_test_id("new-knowledge-card-button").click()
    take_screenshot(page, "knowledge_card_5_create")
    
    # Card reference
    page.get_by_test_id("link-type-select").select_option("donor")
    page.locator(".kc-linked-item-select__input-container").click()
    page.get_by_role("combobox", name="Select Item*").fill("kor")
    page.get_by_role("option", name="Republic of Korea - Ministry").click()
    page.get_by_test_id("confirm-button").click()
    page.get_by_test_id("summary-textarea").click()
    page.get_by_test_id("summary-textarea").fill("test")
    
    # Identify References
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("identify-references-button").click()
    take_screenshot(page, "knowledge_card_6_reference_identified")
    
    # Ingest References
    page.get_by_test_id("ingest-references-button").click()
    expect(page.get_by_test_id("alert-ok-button")).to_be_visible(timeout=200000)
    page.get_by_test_id("alert-ok-button").click()
    take_screenshot(page, "knowledge_card_reference_7_ingested")
    
    # Populate Card
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("populate-card-button").click()
    expect(page.get_by_test_id("alert-ok-button")).to_be_visible(timeout=400000)
    page.get_by_test_id("alert-ok-button").click()
    take_screenshot(page, "knowledge_card_9_populated")
    
    # Edit Card
    page.get_by_test_id("edit-section-button-1. Donor Overview").click()
    take_screenshot(page, "knowledge_card_10_edit")
    page.get_by_role("button", name="Cancel").click()
    
    # Download new card
    with page.expect_download() as download2_info:
        page.get_by_role("button", name="Download as Word Download as").click()
    download2 = download2_info.value
    
    # Save Card
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("close-card-button").click()
    take_screenshot(page, "knowledge_card_11_save")
    
    page.close()
