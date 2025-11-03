import re
import pytest
import os
from playwright.sync_api import Playwright, sync_playwright, Page, expect

def test_peer_review():
    """
    Tests that a user can generate a new proposal and records the video.
    """
    # 1. Setup constants
    email = "test_user@unhcr.org"
    password = "password123"
    base_url = "http://localhost:8502"
    
    # Define where the video will be saved.
    VIDEO_DIR = "playwright/test-results/videos"

    # Ensure the directory exists
    os.makedirs(VIDEO_DIR, exist_ok=True)


    # Use the sync_playwright context manager to launch and control the browser lifecycle
    with sync_playwright() as playwright:
        # Launch browser (use chromium, firefox, or webkit)
        browser = playwright.chromium.launch(headless=False, slow_mo=500)
        
        # 2. Create a new context and set the video recording directory
        # Video recording starts now.
        context = browser.new_context(
            record_video_dir=VIDEO_DIR,
            # Set viewport to a high resolution (e.g., Full HD) for maximum screen space
            viewport={"width": 1920, "height": 1080}, 
            # Set the video output size to match the viewport for best quality
            record_video_size={"width": 1920, "height": 1080}
        )
        
        # 3. Get a new page from the context
        page = context.new_page()

        # -------------------
        # Start of Test Logic
        # -------------------
        page.goto(f"{base_url}/login")
        page.get_by_test_id("email-input").click()
        page.get_by_test_id("email-input").fill(email)
        page.get_by_test_id("password-input").click()
        page.get_by_test_id("password-input").fill(password)
        page.get_by_test_id("submit-button").click()
        expect(page).to_have_url(re.compile(".*dashboard"))        

        # Open Existing Project
        page.get_by_text("Project: Refugee Children Education InitiativeViewTransferDelete Afghanistan -").click()


        # Submit for Peer Review
        page.get_by_role("button", name="Peer Review").click()
        #page.get_by_test_id("user-select-checkbox-5c092577-1230-4473-acf8-b6e3bfb02bca").check()
        page.get_by_text("Test User bis").click()
        page.get_by_test_id("deadline-input").fill("2025-11-19")
        page.screenshot(path="playwright/test-results/peer_review_set.png")
        page.get_by_test_id("confirm-button").click()


        # Log Out
        page.get_by_test_id("user-menu-button").click()
        page.get_by_test_id("logout-button").click()


        # Log in with Peer Review User
        page.get_by_test_id("email-input").click()
        page.get_by_test_id("email-input").fill("test_user_bis@unhcr.org")
        page.get_by_test_id("password-input").click()
        page.get_by_test_id("password-input").fill("password123")
        page.get_by_test_id("submit-button").click()


        # Go to review and select the first one
        page.get_by_test_id("reviews-tab").click()
        page.get_by_test_id("review-card").first.click()


        # Add Comments
        page.get_by_test_id("comment-type-select-Summary").select_option("Clarity")
        page.get_by_test_id("severity-select-Summary").select_option("High")
        page.get_by_test_id("comment-textarea-Summary").click()
        page.get_by_test_id("comment-textarea-Summary").fill("revise this whole part to make it clearer")
        page.screenshot(path="playwright/test-results/peer_review_comment.png")

        page.get_by_test_id("comment-type-select-Rationale").select_option("Impact")
        page.get_by_test_id("comment-textarea-Rationale").click()
        page.get_by_test_id("comment-textarea-Rationale").fill("Stress more the impact")
        
        # Put Review as completed and log out
        page.get_by_test_id("review-completed-button-header").click()
        page.screenshot(path="playwright/test-results/peer_review_completed.png")
        page.get_by_test_id("user-menu-button").click()
        page.get_by_test_id("logout-button").click()


        # Log in with First user
        page.get_by_test_id("email-input").click()
        page.get_by_test_id("email-input").fill("test_user@unhcr.org")
        page.get_by_test_id("password-input").click()
        page.get_by_test_id("password-input").fill("password123")
        page.get_by_test_id("submit-button").click()

        # Open the project
        page.get_by_text("Project: Refugee Children Education InitiativeViewTransferDelete Afghanistan -").click()
        page.screenshot(path="playwright/test-results/peer_review_use.png")
        
        #page.get_by_role("button", name="Pre-Submission").click()
        page.get_by_test_id("logo").click()
        
        # -------------------
        # End of Test Logic
        # -------------------

        # 4. Close the context and browser
        # The video file is saved when the context closes.
        video_path = page.video.path()
        context.close()
        browser.close()
        
        # Optional: Rename the file to something more descriptive
        new_video_path = os.path.join(VIDEO_DIR, "peer-review.webm")
        os.rename(video_path, new_video_path)
        print(f"Video saved successfully to: {new_video_path}")

