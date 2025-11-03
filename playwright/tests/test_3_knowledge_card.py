import re
import pytest
import os
from playwright.sync_api import Playwright, sync_playwright, Page, expect

def test_knowledge_card():
    """
    Tests that a user can create a new knowledge card.
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

        # -------------------
        # View list of cards
        # -------------------        
        expect(page).to_have_url(re.compile(".*dashboard")) 
        page.get_by_test_id("knowledge-tab").click()
        page.screenshot(path="playwright/test-results/knowledge_card_dashboard.png")

        # -------------------
        # Check existing card and download
        # -------------------  

        page.get_by_text("OA7. Community Engagement and").click()

        page.screenshot(path="playwright/test-results/knowledge_card_existing.png")

        # View history
        #page.get_by_role("button", name="View Content History").click()
        #expect(page.get_by_text("Knowledge Card History")).to_be_visible()

        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download as Word Download as").click()
        download = download_info.value

        # -------------------
        # Create new card for Donor 
        # -------------------  
        page.get_by_test_id("logo").click()
        page.get_by_test_id("knowledge-tab").click()
        page.get_by_test_id("new-knowledge-card-button").click()
       # page.goto(f"{base_url}/knowledge-card/new")

        page.screenshot(path="playwright/test-results/10_knowledge_card_create.png")

        # Card reference 
        page.get_by_test_id("link-type-select").select_option("donor")
        page.locator(".css-19bb58m").click()
        page.get_by_role("option", name="State of Kuwait - Kuwait").click()
        page.get_by_test_id("summary-textarea").click()
        page.get_by_test_id("summary-textarea").fill("Test")

    
        # Identify References 
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_test_id("identify-references-button").click()
        page.screenshot(path="playwright/test-results/knowledge_card_reference_identified.png")

        # Manually Add Teference
        # page.get_by_test_id("add-reference-button").click()
        # page.locator("form div").filter(has_text="ReferencesUNHCR Operation").get_by_role("combobox").select_option("Donor Content")
        # page.get_by_role("textbox", name="Summary (optional)").click()
        # page.get_by_role("textbox", name="Summary (optional)").fill("What is it about?")
        # page.get_by_role("button", name="Cancel").click()
        # page.once("dialog", lambda dialog: dialog.dismiss())

        # Ingest References 
        page.once("dialog", lambda dialog: dialog.dismiss())
        expect(page.get_by_test_id("ingest-references-button")).to_be_visible(timeout=500000)
        page.get_by_test_id("ingest-references-button").click()
        page.screenshot(path="playwright/test-results/knowledge_card_reference_ingested.png")

        # # Manage Reference Error
        # page.get_by_text("error").nth(1).click()
        # page.get_by_text("Could not ingest the").click()
        # page.screenshot(path="playwright/test-results/knowledge_card_reference_error.png")
        # page.get_by_role("button", name="Cancel").click()

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
        with page.expect_download() as download2_info:
            page.get_by_role("button", name="Download as Word Download as").click()
        download2 = download2_info.value

        # Save Card
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_test_id("close-card-button").click()
        page.screenshot(path="playwright/test-results/knowledge_card_save.png")


        # -------------------
        # End of Test Logic
        # -------------------

        # 4. Close the context and browser
        # The video file is saved when the context closes.
        video_path = page.video.path()
        context.close()
        browser.close()
        
        # Optional: Rename the file to something more descriptive
        new_video_path = os.path.join(VIDEO_DIR, "knowledge_card.webm")
        os.rename(video_path, new_video_path)
        print(f"Video saved successfully to: {new_video_path}")
