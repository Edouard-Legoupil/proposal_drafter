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
        browser = playwright.chromium.launch(headless=False, slow_mo=1000)
        
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

        # --- 🔑 ISOLATION IMPLEMENTATION START ---
        
        # A. Disable HTTP Network Cache
        context.route("**", lambda route: route.continue_())
        
        # B. Explicitly Clear Cookies (Can be done anytime, but here is fine)
        context.clear_cookies()
        
        # --- 🔑 ISOLATION IMPLEMENTATION END ---


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
        page.screenshot(path="playwright/test-results/knowledge_card_1dashboard.png")

        # -------------------
        # Filter card
        # ------------------- 

        page.get_by_test_id("filter-button").click()
        page.get_by_test_id("knowledge-card-type-filter").select_option("outcome")
        page.screenshot(path="playwright/test-results/knowledge_card_2filter.png")
        page.get_by_test_id("filter-modal-close-button").click()

        # -------------------
        # Check existing card and download
        # -------------------  
        page.get_by_text("Outcome CardOA7. Community Engagement and Participationv1Last Updated: 2025-10-").click()

        page.screenshot(path="playwright/test-results/knowledge_card_3existing.png")

        # Download
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download as Word Download as").click()
        download = download_info.value

        # View history
        page.get_by_test_id("view-history-button").click()
        #expect(page.get_by_text("Knowledge Card History")).to_be_visible()
        page.screenshot(path="playwright/test-results/knowledge_card_4history.png")
        page.get_by_role("button", name="×").click()

        # -------------------
        # Create new card for Donor 
        # -------------------  
        page.get_by_test_id("logo").click()
        page.get_by_test_id("knowledge-tab").click()
        page.get_by_test_id("new-knowledge-card-button").click()

        # page.get_by_test_id("logo").click()
        # page.get_by_text("Project: Refugee Children Education InitiativeViewTransferDelete Afghanistan -").first.click()
        # page.get_by_test_id("manage-knowledge-button").click()
        # page.get_by_test_id("knowledge-card-checkbox-2305e4d0-2e3f-4223-96e7-ce9b3fc471e3").uncheck()
        # page.get_by_test_id("confirm-button").click()
        # page.get_by_test_id("manage-knowledge-button").click()
        page.get_by_test_id("create-new-knowledge-card-button").click()
        page.screenshot(path="playwright/test-results/knowledge_card_5create.png")


        # Card reference   -------
        page.get_by_test_id("link-type-select").select_option("donor")

        page.locator(".kc-linked-item-select__input-container").click()    
        page.get_by_role("option", name="Republic of Korea - Ministry").click()

        page.get_by_test_id("summary-textarea").click()
        page.get_by_test_id("summary-textarea").fill("Test")

    
        # Identify References   -------
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_test_id("identify-references-button").click()
        page.screenshot(path="playwright/test-results/knowledge_card_6reference_identified.png")

        # Remove Reference  -------
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_test_id("remove-reference-button-9").click()

        # Manually Add Reference  -------
        page.get_by_test_id("add-reference-button").click()
        page.get_by_test_id("reference-type-select-10").select_option("Donor Content")
        page.get_by_test_id("reference-summary-textarea-10").click()
        page.get_by_test_id("reference-summary-textarea-10").fill("bla bla bla")
        page.get_by_test_id("cancel-edit-reference-button-10").click()
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_test_id("remove-reference-button-10").click()

        # Ingest References   -------
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_test_id("ingest-references-button").click() 
        # Wait for the loading modal to appear with the correct message, then disappear
        loading_modal_locator = page.locator(".loading-modal")
        expect(loading_modal_locator).to_be_visible()
        expect(page.get_by_text("Reference ingestion started...")).to_be_visible()
        expect(loading_modal_locator).to_be_hidden(timeout=60000)
        page.screenshot(path="playwright/test-results/knowledge_card_reference_7ingested.png")

        # Manage Reference Error   -------
        # page.get_by_text("error").nth(1).click()
        # page.get_by_text("Could not ingest the").click()
        # page.screenshot(path="playwright/test-results/knowledge_card_reference_8error.png")
        # page.get_by_role("button", name="Cancel").click()

        # Populate Card   -------
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_test_id("populate-card-button").click()
        # Wait for the generated content container to be visible, indicating completion
        generated_content_locator = page.get_by_test_id("generated-content-container")
        expect(generated_content_locator).to_be_visible(timeout=180000)
        page.screenshot(path="playwright/test-results/knowledge_card_9populated.png")

        # Edit Card   -------
        page.get_by_test_id("edit-section-button-1. Donor Overview").click()
        page.screenshot(path="playwright/test-results/knowledge_card_10edit.png")
        page.get_by_role("button", name="Cancel").click()
        
        # Download new card   -------
        with page.expect_download() as download2_info:
            page.get_by_role("button", name="Download as Word Download as").click()
        download2 = download2_info.value

        # Save Card   -------
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_test_id("close-card-button").click()
        page.screenshot(path="playwright/test-results/knowledge_card_11save.png")


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
