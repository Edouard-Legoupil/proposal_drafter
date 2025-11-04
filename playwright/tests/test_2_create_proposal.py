import re
import os
from playwright.sync_api import Page, expect

def test_proposal(page: Page):
    """
    Tests that a user can generate a new proposal.
    """
    # 1. Setup constants
    email = "test_user@unhcr.org"
    password = "password123"
    base_url = "http://localhost:8503"
    
    # Mock the API calls
    page.route(f"{base_url}/api/login", lambda route: route.fulfill(status=200))
    page.route(f"{base_url}/api/sso-status", lambda route: route.fulfill(json={"enabled": False}))

    # Create test-results directory if it doesn't exist
    os.makedirs("playwright/test-results", exist_ok=True)

    # -------------------
    # Start of Test Logic
    # -------------------
    page.goto(f"{base_url}/login")
    page.get_by_test_id("email-input").fill(email)
    page.get_by_test_id("password-input").fill(password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))
    page.get_by_test_id("new-proposal-button").click()
    expect(page).to_have_url(re.compile(".*chat"))

    # Fill in the proposal form
    page.get_by_test_id("project-draft-short-name").fill('Project: Refugee Children Education Initiative')
    page.get_by_placeholder('Provide as much details as possible on your initial project idea!').fill('Establishing a comprehensive primary education program for 2,500 refugee children aged 6-14.')

    # Main Outcome (multiselect)
    page.locator(".main-outcome__input-container").click()
    page.get_by_role("combobox", name="Main Outcome").fill("ed")
    page.get_by_role("option", name="OA11. Education").click()
    page.get_by_role("combobox", name="Main Outcome").fill("com")
    page.get_by_role("option", name="OA7. Community Engagement and").click()

    # Beneficiaries
    page.get_by_test_id("beneficiaries-profile").fill("2,500 refugee children aged 6-14")

    # Partner
    page.get_by_test_id("potential-implementing-partner").fill("UNHCR, UNICEF, Save the Children")

    # Geographical Scope (select)
    page.get_by_test_id("geographical-scope").select_option("One Country Operation")

    # Country / Location(s) (creatable select)
    page.locator(".country-location-s__input-container").click()
    page.get_by_role("option", name="Afghanistan").click()

    # Budget Range (creatable select)
    page.locator(".budget-range__input-container").click()
    page.get_by_role("option", name="1M$").click()

    # Duration (creatable select)
    page.locator(".duration__input-container").click()
    page.get_by_role("option", name="12 months").click()

    # Targeted Donor (creatable select)
    page.locator(".targeted-donor__input-container").click()
    page.get_by_role("option", name="Sweden - Ministry for Foreign").click()
    page.screenshot(path="playwright/test-results/proposal_generate.png")

    # Click the "Generate" button
    page.get_by_role('button', name='Generate').click()

    # Wait for the sections to be generated.
    expect(page.get_by_test_id("section-options-0").get_by_role("button", name="edit-section-")).to_be_visible(timeout=500000)

    # Edit section
    page.get_by_role("complementary").get_by_text("Monitoring").click()
    page.get_by_test_id("section-options-4").get_by_role("button", name="edit-section-").click()
    page.screenshot(path="playwright/test-results/proposal_edit_section.png")
    page.get_by_text("Proposal Prompt").click()

    # Regenerate section
    page.get_by_test_id("regenerate-dialog-close-button").click()
    page.get_by_test_id("regenerate-button-rationale").click()
    page.get_by_test_id("regenerate-dialog-close-button").click()

    page.get_by_test_id("regenerate-button-summary").click()
    page.get_by_test_id("regenerate-dialog-prompt-input").fill("Revise this section to fit in 200 characters")
    page.screenshot(path="playwright/test-results/proposal_regenerate_section.png")
    page.get_by_test_id("regenerate-dialog-regenerate-button").click()

    # Download
    with page.expect_download():
        page.get_by_test_id("export-word-button").click()
    with page.expect_download():
        page.get_by_test_id("export-excel-button").click()

    page.get_by_test_id("logo").click()

    # Apply Filter on Proposals
    page.get_by_test_id("filter-button").click()
    page.get_by_test_id("status-filter").select_option("draft")
    page.get_by_test_id("filter-modal-close-button").click()
    page.get_by_test_id("filter-button").click()
    page.get_by_test_id("status-filter").select_option("review")
