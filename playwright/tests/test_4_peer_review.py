import re
import os
from playwright.sync_api import Page, expect

def test_peer_review(page: Page):
    """
    Tests that a user can generate a new proposal and records the video.
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

    # Open Existing Project
    page.get_by_text("Project: Refugee Children Education InitiativeViewTransferDelete Afghanistan -").click()

    # Submit for Peer Review
    page.get_by_role("button", name="Peer Review").click()
    page.get_by_text("Test User bis").click()
    page.get_by_test_id("deadline-input").fill("2025-11-19")
    page.screenshot(path="playwright/test-results/peer_review_set.png")
    page.get_by_test_id("confirm-button").click()

    # Log Out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Log in with Peer Review User
    page.get_by_test_id("email-input").fill("test_user_bis@unhcr.org")
    page.get_by_test_id("password-input").fill("password123")
    page.get_by_test_id("submit-button").click()

    # Go to review and select the first one
    page.get_by_test_id("reviews-tab").click()
    page.get_by_test_id("review-card").first.click()

    # Add Comments
    page.get_by_test_id("comment-type-select-Summary").select_option("Clarity")
    page.get_by_test_id("severity-select-Summary").select_option("High")
    page.get_by_test_id("comment-textarea-Summary").fill("revise this whole part to make it clearer")
    page.screenshot(path="playwright/test-results/peer_review_comment.png")

    page.get_by_test_id("comment-type-select-Rationale").select_option("Impact")
    page.get_by_test_id("comment-textarea-Rationale").fill("Stress more the impact")

    # Put Review as completed and log out
    page.get_by_test_id("review-completed-button-header").click()
    page.screenshot(path="playwright/test-results/peer_review_completed.png")
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Log in with First user
    page.get_by_test_id("email-input").fill("test_user@unhcr.org")
    page.get_by_test_id("password-input").fill("password123")
    page.get_by_test_id("submit-button").click()

    # Open the project
    page.get_by_text("Project: Refugee Children Education InitiativeViewTransferDelete Afghanistan -").click()
    page.screenshot(path="playwright/test-results/peer_review_use.png")

    page.get_by_test_id("logo").click()
