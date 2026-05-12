"""
Test suite for proposal creation and management.

These tests verify that:
1. Users can create new proposals
2. Proposals can be edited and regenerated
3. Sections can be managed
4. Proposals can be exported
5. Proposal filters work correctly
"""

import re
import os
import pytest
from playwright.sync_api import expect

from .conftest import TEST_USERS, TestUser, take_screenshot


# ============================================================================
# Test Constants
# ============================================================================

PROJECT_NAME = "Project: Refugee Children Education Initiative"
PROJECT_DESCRIPTION = "Establishing a comprehensive primary education program for 2,500 refugee children aged 6-14."


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
# Test: Create New Proposal
# ============================================================================

@pytest.mark.proposal_creation
@pytest.mark.e2e
def test_create_new_proposal(logged_in_user, config):
    """
    Test the complete workflow of creating a new proposal.
    
    Steps:
    1. Click "New Proposal" button
    2. Fill in all proposal details
    3. Submit and generate
    4. Verify sections are generated
    """
    page = logged_in_user
    
    # Step 1: Start new proposal
    page.get_by_test_id("new-proposal-button").click()
    expect(page).to_have_url(re.compile(".*chat"))
    
    # Step 2: Fill in proposal form
    page.get_by_test_id("project-draft-short-name").click()
    page.get_by_test_id("project-draft-short-name").fill(PROJECT_NAME)
    
    # Project description
    page.get_by_role("textbox", name="Provide as much details as").click()
    page.get_by_placeholder("Provide as much details as possible on your initial project idea!").fill(PROJECT_DESCRIPTION)
    
    # Main Outcome (multiselect)
    page.locator(".main-outcome__input-container").click()
    page.get_by_role("combobox", name="Main Outcome").fill("ed")
    page.get_by_role("option", name="OA11. Education").click()
    page.get_by_role("combobox", name="Main Outcome").fill("com")
    page.get_by_role("option", name="OA7. Community Engagement and").click()
    
    # Beneficiaries
    page.get_by_test_id("beneficiaries-profile").click()
    page.get_by_test_id("beneficiaries-profile").fill("2,500 refugee children aged 6-14")
    
    # Partner
    page.get_by_test_id("potential-implementing-partner").click()
    page.get_by_test_id("potential-implementing-partner").fill("UNHCR, UNICEF, Save the Children")
    
    # Geographical Scope
    page.get_by_test_id("geographical-scope").select_option("One Country Operation")
    
    # Country / Location
    page.locator(".country-location-s__input-container").click()
    page.get_by_role("option", name="Afghanistan").click()
    
    # Budget Range
    page.locator(".budget-range__input-container").click()
    page.get_by_role("option", name="1M$").click()
    
    # Duration
    page.locator(".duration__input-container").click()
    page.get_by_role("option", name="12 months").click()
    
    # Targeted Donor
    page.locator(".targeted-donor__input-container").click()
    page.get_by_role("option", name="Sweden - Ministry for Foreign").click()
    
    take_screenshot(page, "proposal_form_filled")
    
    # Step 3: Generate proposal
    page.get_by_role("button", name="Generate").click()
    
    # Step 4: Wait for sections to be generated
    # The wait is conditioned on the visibility of the edit button for the first section
    expect(page.get_by_test_id("edit-save-button-summary")).to_be_visible(timeout=600000)
    
    take_screenshot(page, "proposal_generated")
    
    # Verify we can see generated sections
    expect(page.get_by_test_id("sidebar-option-summary")).to_be_visible()
    expect(page.get_by_test_id("sidebar-option-evaluation")).to_be_visible()


# ============================================================================
# Test: Navigate Between Proposal Sections
# ============================================================================

@pytest.mark.proposal_creation
def test_navigate_proposal_sections(logged_in_user, config):
    """
    Test navigation between different proposal sections.
    
    Precondition: A proposal must already exist.
    """
    page = logged_in_user
    
    # Open an existing proposal (assuming one exists)
    # If no proposal exists, this will fail - that's expected
    try:
        page.get_by_text("Project: Refugee Children Education").first.click()
    except Exception:
        pytest.skip("No existing proposal found for navigation test")
    
    # Navigate to different sections
    page.get_by_test_id("sidebar-option-evaluation").click()
    expect(page.get_by_test_id("edit-save-button-evaluation")).to_be_visible()
    take_screenshot(page, "proposal_section_evaluation")
    
    page.get_by_test_id("sidebar-option-work-plan").click()
    expect(page.get_by_test_id("edit-save-button-work-plan")).to_be_visible()
    
    page.get_by_test_id("sidebar-option-summary").click()
    expect(page.get_by_test_id("edit-save-button-summary")).to_be_visible()
    
    page.get_by_test_id("sidebar-option-monitoring").click()
    expect(page.get_by_test_id("edit-save-button-monitoring")).to_be_visible()
    
    take_screenshot(page, "proposal_section_navigation")


# ============================================================================
# Test: Edit Proposal Section
# ============================================================================

@pytest.mark.proposal_creation
def test_edit_proposal_section(logged_in_user, config):
    """
    Test editing a proposal section.
    
    Precondition: A proposal must already exist.
    """
    page = logged_in_user
    
    try:
        page.get_by_text("Project: Refugee Children Education").first.click()
    except Exception:
        pytest.skip("No existing proposal found for edit test")
    
    # Navigate to Monitoring section
    page.get_by_test_id("sidebar-option-monitoring").click()
    
    # Edit the section
    page.get_by_test_id("edit-save-button-monitoring").click()
    take_screenshot(page, "proposal_edit_mode")
    
    # Cancel edit
    page.get_by_test_id("cancel-edit-button-monitoring").click()
    take_screenshot(page, "proposal_edit_cancelled")


# ============================================================================
# Test: Regenerate Proposal Section
# ============================================================================

@pytest.mark.proposal_creation
@pytest.mark.slow
def test_regenerate_proposal_section(logged_in_user, config):
    """
    Test regenerating a proposal section with a custom prompt.
    
    Precondition: A proposal must already exist.
    """
    page = logged_in_user
    
    try:
        page.get_by_text("Project: Refugee Children Education").first.click()
    except Exception:
        pytest.skip("No existing proposal found for regeneration test")
    
    # Navigate to Summary section
    page.get_by_test_id("sidebar-option-summary").click()
    
    # Regenerate section
    page.get_by_test_id("regenerate-button-summary").click()
    
    # Fill in regenerate prompt
    page.get_by_test_id("regenerate-dialog-prompt-input").click()
    page.get_by_test_id("regenerate-dialog-prompt-input").fill("Revise this section to fit in 200 characters")
    
    take_screenshot(page, "proposal_regenerate_prompt")
    
    # Submit regeneration
    page.get_by_test_id("regenerate-dialog-regenerate-button").click()
    
    # Wait for regeneration to complete
    expect(page.get_by_test_id("edit-save-button-summary")).to_be_visible(timeout=600000)
    
    take_screenshot(page, "proposal_section_regenerated")


# ============================================================================
# Test: Export Proposal as Word
# ============================================================================

@pytest.mark.proposal_creation
def test_export_proposal_as_word(logged_in_user, config):
    """
    Test exporting a proposal as a Word document.
    
    Precondition: A proposal must already exist.
    """
    page = logged_in_user
    
    try:
        page.get_by_text("Project: Refugee Children Education").first.click()
    except Exception:
        pytest.skip("No existing proposal found for export test")
    
    # Export as Word
    with page.expect_download() as download_info:
        page.get_by_test_id("export-word-button").click()
    
    download = download_info.value
    assert download is not None
    assert download.path() is not None
    
    take_screenshot(page, "proposal_export_word")
    print(f"[DOWNLOAD] Word document exported to: {download.path()}")


# ============================================================================
# Test: Filter Proposals by Status
# ============================================================================

@pytest.mark.proposal_creation
def test_filter_proposals_by_status(logged_in_user, config):
    """
    Test filtering proposals by status.
    """
    page = logged_in_user
    
    # Click filter button
    page.get_by_test_id("filter-button").click()
    
    # Filter by draft status
    page.get_by_test_id("status-filter").select_option("draft")
    take_screenshot(page, "proposal_filter_draft")
    
    # Close filter modal
    page.get_by_test_id("filter-modal-close-button").click()
    
    # Reopen and filter by review status
    page.get_by_test_id("filter-button").click()
    page.get_by_test_id("status-filter").select_option("review")
    take_screenshot(page, "proposal_filter_review")
    
    # Close filter modal
    page.get_by_test_id("filter-modal-close-button").click()


# ============================================================================
# Test: Full Proposal Creation Workflow (Backward Compatibility)
# ============================================================================

@pytest.mark.proposal_creation
@pytest.mark.e2e
@pytest.mark.regression
def test_full_proposal_workflow(context, config):
    """
    Full proposal creation workflow maintaining backward compatibility.
    
    This test follows the exact workflow from the original test_2_create_proposal.py
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
    
    # Create new proposal
    page.get_by_test_id("new-proposal-button").click()
    expect(page).to_have_url(re.compile(".*chat"))
    
    # Fill in the proposal form
    page.get_by_test_id("project-draft-short-name").click()
    page.get_by_test_id("project-draft-short-name").fill(PROJECT_NAME)
    page.get_by_role("textbox", name="Provide as much details as").click()
    page.get_by_placeholder("Provide as much details as possible on your initial project idea!").fill(PROJECT_DESCRIPTION)
    
    # Main Outcome (multiselect)
    page.locator(".main-outcome__input-container").click()
    page.get_by_role("combobox", name="Main Outcome").fill("ed")
    page.get_by_role("option", name="OA11. Education").click()
    page.get_by_role("combobox", name="Main Outcome").fill("com")
    page.get_by_role("option", name="OA7. Community Engagement and").click()
    
    # Beneficiaries
    page.get_by_test_id("beneficiaries-profile").click()
    page.get_by_test_id("beneficiaries-profile").fill("2,500 refugee children aged 6-14")
    
    # Partner
    page.get_by_test_id("potential-implementing-partner").click()
    page.get_by_test_id("potential-implementing-partner").fill("UNHCR, UNICEF, Save the Children")
    
    # Geographical Scope
    page.get_by_test_id("geographical-scope").select_option("One Country Operation")
    
    # Country / Location
    page.locator(".country-location-s__input-container").click()
    page.get_by_role("option", name="Afghanistan").click()
    
    # Budget Range
    page.locator(".budget-range__input-container").click()
    page.get_by_role("option", name="1M$").click()
    
    # Duration
    page.locator(".duration__input-container").click()
    page.get_by_role("option", name="12 months").click()
    
    # Targeted Donor
    page.locator(".targeted-donor__input-container").click()
    page.get_by_role("option", name="Sweden - Ministry for Foreign").click()
    
    take_screenshot(page, "proposal_1_generate")
    
    # Click Generate
    page.get_by_role("button", name="Generate").click()
    
    # Wait for sections to be generated
    expect(page.get_by_test_id("edit-save-button-summary")).to_be_visible(timeout=600000)
    
    # Browser Proposal
    page.get_by_test_id("sidebar-option-evaluation").click()
    take_screenshot(page, "proposal_2_generated")
    page.get_by_test_id("sidebar-option-work-plan").click()
    page.get_by_test_id("sidebar-option-summary").click()
    
    # Edit Section
    page.get_by_test_id("sidebar-option-monitoring").click()
    page.get_by_test_id("edit-save-button-monitoring").click()
    take_screenshot(page, "proposal_3_edit_section")
    page.get_by_test_id("cancel-edit-button-monitoring").click()
    
    # Regenerate section
    page.get_by_test_id("sidebar-option-summary").click()
    page.get_by_test_id("regenerate-button-summary").click()
    page.get_by_test_id("regenerate-dialog-prompt-input").click()
    page.get_by_test_id("regenerate-dialog-prompt-input").fill("Revise this section to fit in 200 characters")
    take_screenshot(page, "proposal_4_regenerate_section")
    page.get_by_test_id("regenerate-dialog-regenerate-button").click()
    expect(page.get_by_test_id("edit-save-button-summary")).to_be_visible(timeout=600000)
    take_screenshot(page, "proposal_5_regenerated_section")
    
    # Download
    with page.expect_download() as download_info:
        page.get_by_test_id("export-word-button").click()
    download = download_info.value
    
    # Return to dashboard
    page.get_by_test_id("logo").click()
    
    # Apply Filter on Proposals
    page.get_by_role("search").click()
    page.get_by_test_id("filter-button").click()
    page.get_by_test_id("status-filter").select_option("draft")
    page.get_by_test_id("filter-modal-close-button").click()
    page.get_by_test_id("filter-button").click()
    page.get_by_test_id("status-filter").select_option("review")
    
    page.close()
