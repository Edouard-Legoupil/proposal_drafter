import re
import pytest
from playwright.sync_api import Page, expect

def test_create_new_knowledge_card(page: Page):
    """
    Tests that a user can create a new knowledge card.
    """
    email = "test_user@unhcr.org"
    password = "password123"
    base_url = "http://localhost:8502"

    page.goto(f"{base_url}/login")
    page.get_by_test_id("email-input").fill(email)
    page.get_by_test_id("password-input").fill(password)
    page.get_by_test_id("submit-button").click()

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

    # ---------------------
    #context.close()
    #browser.close()


#     import re
# from playwright.sync_api import Playwright, sync_playwright, expect


# def run(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#     page.goto("http://localhost:8502/")
#     page.get_by_test_id("email-input").click()
#     page.get_by_test_id("email-input").fill("test_user@unhcr.org")
#     page.get_by_test_id("password-input").click()
#     page.get_by_test_id("password-input").fill("password123")
#     page.get_by_test_id("submit-button").click()

#     page.goto("http://localhost:8502/dashboard")

#     # ---------------------
#     context.close()
#     browser.close()


# with sync_playwright() as playwright:
#     run(playwright)
