import re
import pytest
from playwright.sync_api import Page, expect

def test_create_new_knowledge_card(page: Page):
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
        expect(page).to_have_url(re.compile(".*dashboard"))        
        page.get_by_test_id("new-proposal-button").click()        
        expect(page).to_have_url(re.compile(".*chat"))

        expect(page).to_have_url(re.compile(".*dashboard"))
        page.get_by_test_id("knowledge-tab").click()

        page.screenshot(path="playwright/test-results/9_knowledge_card.png")

        page.get_by_test_id("new-knowledge-card-button").click()

        page.goto(f"{base_url}/knowledge-card/new")
        page.screenshot(path="playwright/test-results/10_knowledge_card_create.png")


    
        page.get_by_test_id("reference-type-select-0").select_option("Evaluation Report")
        page.get_by_test_id("reference-url-input-0").click()
        page.get_by_test_id("reference-url-input-0").fill("https://www.unhcr.org/media/brazil-country-strategy-evaluation")
        page.get_by_test_id("add-reference-button").click()
        page.get_by_test_id("remove-reference-button-1").click()
        page.get_by_test_id("identify-references-button").click()



    #    page.get_by_test_id("link-type-select").select_option("outcome")
    #    page.get_by_role("option", name="OA13-Livelihoods").click()


        page.get_by_test_id("link-type-select").select_option("outcome")
        page.locator(".css-19bb58m").click()
        page.get_by_role("option", name="OA13-Livelihoods").click()

        page.get_by_test_id("title-input").click()
        page.get_by_test_id("title-input").fill("test card outcome")

    

        page.get_by_test_id("summary-textarea").click()
        page.get_by_test_id("summary-textarea").fill("test card outcome")

    
        page.get_by_test_id("populate-card-button").click()
        page.get_by_test_id("save-card-button").click()
        page.once("dialog", lambda dialog: dialog.dismiss())
        
        page.screenshot(path="playwright/test-results/11_knowledge_card_save.png")



    # Navigate to the knowledge card
        page.goto("http://localhost:8511/knowledge-card/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", timeout=60000)
        page.wait_for_selector('[data-testid="add-reference-button"]')

        # Add a new reference
        page.get_by_test_id("add-reference-button").click()
        page.wait_for_timeout(500)
        page.get_by_placeholder("https://example.com").fill("https://www.google.com")
        page.locator('select').nth(1).select_option('Social Media')
        page.get_by_placeholder("Summary").fill("Test summary")
        page.locator(".kc-reference-edit-actions > button:first-child").click()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("https://www.google.com")).to_be_visible(timeout=10000)
        expect(page.get_by_text("Test summary")).to_be_visible(timeout=10000)

        # Edit the new reference
        page.get_by_role("button").nth(5).click()
        page.wait_for_timeout(500)
        page.get_by_placeholder("https://example.com").fill("https://www.unhcr.org/social")
        page.get_by_placeholder("Summary").fill("Updated test summary")
        page.locator(".kc-reference-edit-actions > button:first-child").click()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("https://www.unhcr.org/social")).to_be_visible(timeout=10000)
        expect(page.get_by_text("Updated test summary")).to_be_visible(timeout=10000)

        # Delete a reference
        page.get_by_role("button").nth(6).click()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("https://www.unhcr.org/social")).not_to_be_visible(timeout=10000)

        # View history
        page.get_by_role("button", name="View Content History").click()
        expect(page.get_by_text("Knowledge Card History")).to_be_visible()

        # Take a screenshot
        page.screenshot(path="jules-scratch/verification/knowledge_card_redesign.png")


        # # Expect the page to have the correct heading
        # expect(page.get_by_role("heading", name="Create New Knowledge Card")).to_be_visible()

        # # Fill in the form
        # page.get_by_label('Link To').select_option(label='Donor')

        # # The react-select component can be tricky. These selectors are based on the JS test.
        # # They might need to be adjusted if they are not stable.
        # # The #react-select-2-input is particularly brittle.
        # page.locator('.react-select__control').click()
        # # A more robust selector would be to target the input based on the control's id
        # # but for now we will stick to the original test's locator.
        # page.locator('input[id^="react-select-"]').fill('New Donor')
        # page.get_by_text('Create "New Donor"').click()

        # page.get_by_label('Title*').fill('Test Knowledge Card from Playwright')
        # page.get_by_label('Description').fill('This is a test knowledge card created by a Playwright test.')
        # page.get_by_placeholder('https://example.com').fill('https://www.unhcr.org')
        # page.get_by_placeholder('Reference Type').fill('Test Reference')

        # # Set up a handler for the dialog that is expected to appear
        # page.on('dialog', lambda dialog: dialog.accept())

        # # Click the save button
        # page.get_by_role('button', name='Save Card').click()

        # # After saving, the user should be redirected to the knowledge card list
        # expect(page).to_have_url(re.compile(".*knowledge-cards"))
        # expect(page.get_by_text("Test Knowledge Card from Playwright")).to_be_visible()

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
