import re
import os
from playwright.sync_api import Page, expect

def test_knowledge_card(page: Page):
    """
    Tests that a user can create a new knowledge card.
    """
    # 1. Setup constants
    email = "test_user@unhcr.org"
    password = "password123"
    base_url = "http://localhost:8503"

    # Mock the API calls
    page.route(f"{base_url}/api/login", lambda route: route.fulfill(status=200))
    page.route(f"{base_url}/api/sso-status", lambda route: route.fulfill(json={"enabled": False}))
    page.route(f"{base_url}/api/list-drafts", lambda route: route.fulfill(json={"drafts": []}))
    page.route(f"{base_url}/api/proposals/reviews", lambda route: route.fulfill(json={"reviews": []}))
    page.route(f"{base_url}/api/knowledge-cards", lambda route: route.fulfill(json={"knowledge_cards": [{"id": "1", "outcome_name": "OA7. Community Engagement and", "donor_name": None, "field_context_name": None, "updated_at": "2024-01-01T00:00:00"}]}))
    page.route(f"{base_url}/api/users", lambda route: route.fulfill(json={"users": []}))
    page.route(f"{base_url}/api/outcomes", lambda route: route.fulfill(json={"outcomes": []}))
    page.route(f"{base_url}/api/donors", lambda route: route.fulfill(json={"donors": [{"id": "1", "donor_name": "State of Kuwait - Kuwait"}]}))
    page.route(f"{base_url}/api/field-contexts", lambda route: route.fulfill(json={"field_contexts": []}))

    # Create test-results directory if it doesn't exist
    os.makedirs("playwright/test-results", exist_ok=True)

    # -------------------
    # Start of Test Logic
    # -------------------
    page.goto(f"{base_url}/login")
    page.get_by_test_id("email-input").fill(email)
    page.get_by_test_id("password-input").fill(password)
    page.get_by_test_id("submit-button").click()

    # View list of cards
    expect(page).to_have_url(re.compile(".*dashboard"))
    expect(page.get_by_test_id("knowledge-tab")).to_be_visible()
    page.get_by_test_id("knowledge-tab").click()
    page.screenshot(path="playwright/test-results/knowledge_card_dashboard.png")

    # Check existing card and download
    page.get_by_text("OA7. Community Engagement and").click()
    page.screenshot(path="playwright/test-results/knowledge_card_existing.png")

    with page.expect_download():
        page.get_by_role("button", name="Download as Word Download as").click()

    # Create new card for Donor
    page.get_by_test_id("logo").click()
    page.get_by_test_id("knowledge-tab").click()
    page.get_by_test_id("new-knowledge-card-button").click()

    page.screenshot(path="playwright/test-results/10_knowledge_card_create.png")

    # Card reference
    page.get_by_test_id("link-type-select").select_option("donor")
    page.locator(".css-19bb58m").click()
    page.get_by_role("option", name="State of Kuwait - Kuwait").click()
    page.get_by_test_id("summary-textarea").fill("Test")

    # Identify References
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("identify-references-button").click()
    page.screenshot(path="playwright/test-results/knowledge_card_reference_identified.png")

    # Ingest References
    page.once("dialog", lambda dialog: dialog.dismiss())
    expect(page.get_by_test_id("ingest-references-button")).to_be_visible(timeout=500000)
    page.get_by_test_id("ingest-references-button").click()
    page.screenshot(path="playwright/test-results/knowledge_card_reference_ingested.png")

    # Populate Card
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("populate-card-button").click()
    page.screenshot(path="playwright/test-results/knowledge_card_populated.png")

    # Edit Card
    page.get_by_test_id("edit-section-button-1. Donor Overview").click()
    page.get_by_text("The State of Kuwait is").click()
    page.screenshot(path="playwright/test-results/knowledge_card_edit.png")
    page.get_by_role("button", name="Cancel").click()
    
    # Download new card
    with page.expect_download():
        page.get_by_role("button", name="Download as Word Download as").click()

    # Save Card
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_test_id("close-card-button").click()
    page.screenshot(path="playwright/test-results/knowledge_card_save.png")
