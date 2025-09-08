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
    page.get_by_role("textbox", name="Project Draft Short name*").fill('Refugee Children Education Initiative - Kenya')
    page.get_by_placeholder('Provide as much details as possible on your initial project idea!').fill('Establishing a comprehensive primary education program for 2,500 refugee children aged 6-14.')

    # Main Outcome (multiselect)

    page.locator(".main-outcome__input-container").click()
    page.get_by_role("option", name="OA11-Education").click()
    page.locator(".main-outcome__input-container").click()
    page.get_by_role("option", name="OA7-Community").click()

    page.get_by_test_id("beneficiaries-profile").click()
    page.get_by_test_id("beneficiaries-profile").fill("Refugee Children")
    
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
    page.get_by_role("option", name="United States of America -").click()
    
    # Click the "Generate" button  -------
    page.get_by_role('button', name='Generate').click()

    # Wait for the sections to be generated. This can be slow.  -------
    #expect(page.locator('h2:has-text("Executive Summary")')).to_be_visible(timeout=120000)

    #expect(page.locator('h2:has-text("Background and Needs Assessment")')).to_be_visible(timeout=120000)
   # Take screenshot  
    page.screenshot(path="playwright/test-results/5_proposal_created.png")

   # browser.close()