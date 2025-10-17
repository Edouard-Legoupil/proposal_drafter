import re
import pytest
from playwright.sync_api import Page, expect

def test_generate_new_proposal(page: Page):
    """
    Tests that a user can generate a new proposal.
    """
    email = "test_user@unhcr.org"
    password = "password123"
    base_url = "http://localhost:8502"

    page.goto(f"{base_url}/login")
    page.get_by_test_id("email-input").fill(email)
    page.get_by_test_id("password-input").fill(password)
    page.get_by_test_id("submit-button").click()

    expect(page).to_have_url(re.compile(".*dashboard"))
    
    page.get_by_test_id("new-proposal-button").click()
    
    expect(page).to_have_url(re.compile(".*chat"))

   # Take screenshot 
    page.screenshot(path="playwright/test-results/4_generate_proposal.png")


    # Fill in the proposal form
    page.get_by_role("textbox", name="Project Draft Short name*").fill('Refugee Children Education Initiative')
    page.get_by_placeholder('Provide as much details as possible on your initial project idea!').fill('Establishing a comprehensive primary education program for 2,500 refugee children aged 6-14.')

    # Main Outcome (multiselect)
    page.locator("label").filter(has_text="Main Outcome*").click()
    page.locator(".main-outcome__input-container").click()
    page.get_by_role("option", name="OA11-Education").click()
    page.locator(".main-outcome__input-container").click()
    page.get_by_role("option", name="OA7-Community").click()

    page.get_by_test_id("beneficiaries-profile").click()
    page.get_by_test_id("beneficiaries-profile").fill("2,500 refugee children aged 6-14")
    
    page.get_by_test_id("potential-implementing-partner").click()
    page.get_by_test_id("potential-implementing-partner").fill("UNHCR, UNICEF, Save the Children")

    # Geographical Scope (select)  -------
    page.get_by_label('Geographical Scope').select_option(label='One Country Operation')

    # Country / Location(s) (creatable select)  
    page.locator(".country-location-s__input-container").click()
    page.get_by_role("option", name="Colombia").click()


    # Budget Range (creatable select) -------
    page.locator(".budget-range__input-container").click()
    page.get_by_role("option", name="1M$").click()

    # Duration (creatable select)  -------
    page.locator(".duration__input-container").click()
    page.get_by_role("option", name="12 months").click()

    # Targeted Donor (creatable select)  -------
    page.locator(".targeted-donor__input-container").click()
    page.get_by_role("option", name="Sweden - Ministry for Foreign").click()
    
    # Click the "Generate" button  -------
    page.get_by_role('button', name='Generate').click()

    # Wait for the sections to be generated. This can be slow.  -------
    expect(page.get_by_role("button", name="Download Document")).to_be_visible(timeout=120000)
   # Take screenshot  
#    page.screenshot(path="playwright/test-results/5_proposal_created.png")

#        with page.expect_download() as download_info:
 #       page.get_by_role("button", name="Download Document").click()
 #   download = download_info.value
 #   page.get_by_role("button", name="Peer Review").click()
   # page.get_by_test_id("user-select-checkbox-be7ebe30-fcc8-442f-993b-dd89b8d61dfb").check()
    #page.get_by_test_id("deadline-input").fill("2025-09-10")
    #page.get_by_test_id("confirm-button").click()



    page.get_by_role("button", name="Peer Review").click()
    page.get_by_text("Test User bis").click()
    page.get_by_test_id("deadline-input").fill("2025-09-11")
    # Take screenshot  
    page.screenshot(path="playwright/test-results/6_peer_review.png")
    page.get_by_test_id("confirm-button").click()

    page.get_by_test_id("logo").click()
    page.get_by_role("article").filter(has_text="Refugee Children Education Initiative Establishing a comprehensive primary").get_by_test_id("project-options-button").click()

    #expect(page.locator('h2:has-text("Background and Needs Assessment")')).to_be_visible(timeout=120000)

   # browser.close()
