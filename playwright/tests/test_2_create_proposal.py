import re
import pytest
import os
from playwright.sync_api import Playwright, sync_playwright, Page, expect

def test_proposal():
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
        page.get_by_test_id("new-proposal-button").click()        
        expect(page).to_have_url(re.compile(".*chat"))

        # Fill in the proposal form ------- 
        page.get_by_test_id("project-draft-short-name").click()
        page.get_by_test_id("project-draft-short-name").fill('Project: Refugee Children Education Initiative')
        page.get_by_role("textbox", name="Provide as much details as").click()
        page.get_by_placeholder('Provide as much details as possible on your initial project idea!').fill('Establishing a comprehensive primary education program for 2,500 refugee children aged 6-14.')

        # Main Outcome (multiselect) ------- 
        page.locator(".main-outcome__input-container").click()
        page.get_by_role("combobox", name="Main Outcome").fill("ed")
        page.get_by_role("option", name="OA11. Education").click()
        page.get_by_role("combobox", name="Main Outcome").fill("com")
        page.get_by_role("option", name="OA7. Community Engagement and").click()

        # Beneficiaries ------- 
        page.get_by_test_id("beneficiaries-profile").click()
        page.get_by_test_id("beneficiaries-profile").fill("2,500 refugee children aged 6-14")
        
        # Partner ------- 
        page.get_by_test_id("potential-implementing-partner").click()
        page.get_by_test_id("potential-implementing-partner").fill("UNHCR, UNICEF, Save the Children")

        # Geographical Scope (select)  ------- 
        page.get_by_test_id("geographical-scope").select_option("One Country Operation")
      
        # Country / Location(s) (creatable select)  
        page.locator(".country-location-s__input-container").click()
        #page.get_by_role("option", name="Colombia").click()
        page.get_by_role("option", name="Afghanistan").click()    

        # Budget Range (creatable select) -------
        page.locator(".budget-range__input-container").click()
        page.get_by_role("option", name="1M$").click()

        # Duration (creatable select)  -------
        page.locator(".duration__input-container").click()
        page.get_by_role("option", name="12 months").click()

        # Targeted Donor (creatable select)  -------
        page.locator(".targeted-donor__input-container").click()
        page.get_by_role("option", name="Sweden - Ministry for Foreign").click()
        page.screenshot(path="playwright/test-results/proposal_1generate.png")
        
        # Click the "Generate" button  -------
        page.get_by_role('button', name='Generate').click()

        # Wait for the sections to be generated. This can be slow.  -------
        # The wait is now conditioned on the visibility of the edit button for the first section.
        expect(page.get_by_test_id("edit-save-button-summary")).to_be_visible(timeout=500000)
        
        # Browser Proposal -----
        page.get_by_test_id("sidebar-option-evaluation").click()
        page.screenshot(path="playwright/test-results/proposal_2generated.png")
        page.get_by_test_id("sidebar-option-work-plan").click()
        page.get_by_test_id("sidebar-option-summary").click()

        # Edit Section  -------
        page.get_by_test_id("sidebar-option-monitoring").click()
        page.get_by_test_id("edit-save-button-monitoring").click()
        page.screenshot(path="playwright/test-results/proposal_3edit_section.png")
        page.get_by_test_id("cancel-edit-button-monitoring").click()
        
        # Renerate section  -------
        page.get_by_test_id("sidebar-option-summary").click()
        page.get_by_test_id("regenerate-button-summary").click()
        page.get_by_test_id("regenerate-dialog-prompt-input").click()
        page.get_by_test_id("regenerate-dialog-prompt-input").fill("Revise this section to fit in 200 characters")
        page.screenshot(path="playwright/test-results/proposal_4regenerate_section.png")
        page.get_by_test_id("regenerate-dialog-regenerate-button").click()
        expect(page.get_by_test_id("edit-save-button-summary")).to_be_visible(timeout=500000)
        page.screenshot(path="playwright/test-results/proposal_5regenerated_section.png")

        # Download  -------
        with page.expect_download() as download1_info:
            page.get_by_test_id("export-word-button").click()
        download1 = download1_info.value
        # with page.expect_download() as download_info:
        #     page.get_by_test_id("export-excel-button").click()
        # download = download_info.value

        page.get_by_test_id("logo").click()
        #page.get_by_role("article").filter(has_text="Refugee Children Education Initiative Establishing a comprehensive #primary").get_by_test_id("project-options-button").click()

        # Apply Filter on Proposals  -------
        page.get_by_role("search").click()
        page.get_by_test_id("filter-button").click()
        page.get_by_test_id("status-filter").select_option("draft")
        page.get_by_test_id("filter-modal-close-button").click()
        page.get_by_test_id("filter-button").click()
        page.get_by_test_id("status-filter").select_option("review")

        # -------------------
        # End of Test Logic
        # -------------------

        # 4. Close the context and browser
        # The video file is saved when the context closes.
        video_path = page.video.path()
        context.close()
        browser.close()
        
        # Optional: Rename the file to something more descriptive
        new_video_path = os.path.join(VIDEO_DIR, "Proposal_Generation.webm")
        os.rename(video_path, new_video_path)
        print(f"Video saved successfully to: {new_video_path}")

