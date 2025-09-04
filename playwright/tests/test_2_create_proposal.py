import re
import pytest
from playwright.sync_api import Page, expect

def test_generate_new_proposal(page: Page):
    """
    Tests that a user can generate a new proposal.
    """
    email = "testuser@unhcr.org"
    password = "password123"
    base_url = "http://localhost:8502"

    page.goto(f"{base_url}/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="LOGIN").click()

    expect(page).to_have_url(re.compile(".*dashboard"))
    
    page.get_by_role('button', name='Start a new proposal').click()
    
    expect(page).to_have_url(re.compile(".*chat"))

   # Take screenshot 
    page.screenshot(path="playwright/test-results/4_generate_proposal.png")


    # Fill in the proposal form
    page.get_by_label('Project Draft Short name').fill('Test Project from Playwright')
    page.get_by_placeholder('Provide as much details as possible on your initial project idea!').fill('Build school.')

    # Main Outcome (multiselect)
    page.locator('.creatable-select').filter(has_text='Main Outcome').click()
    page.get_by_text('Outcome 1', exact=True).click()

    page.get_by_label('Beneficiaries Profile').fill('Refugee Kids')
    
    page.get_by_label('Potential Implementing Partner').fill('UNICEF')
    
    # Geographical Scope (select)
    page.get_by_label('Geographical Scope').select_option(label='One Country Operation')

    # Country / Location(s) (creatable select)
    page.locator('div').filter(has_text=re.compile(r'^\*Country / Location\(s\)$')).locator('div').nth(1).click()
    page.get_by_text('Country 1', exact=True).click()

    # Budget Range (creatable select)
    page.locator('div').filter(has_text=re.compile(r'^\*Budget Range$')).locator('div').nth(1).click()
    page.get_by_text('100k$').click()

    # Duration (creatable select)
    page.locator('div').filter(has_text=re.compile(r'^\*Duration$')).locator('div').nth(1).click()
    page.get_by_text('6 months', exact=True).click()

    # Targeted Donor (creatable select)
    page.locator('div').filter(has_text=re.compile(r'^\*Targeted Donor$')).locator('div').nth(1).click()
    page.get_by_text('UNHCR', exact=True).click()
    
    # Click the "Generate" button
    page.get_by_role('button', name='Generate').click()

    # Wait for the sections to be generated. This can be slow.
    expect(page.locator('h2:has-text("Executive Summary")')).to_be_visible(timeout=120000)

    expect(page.locator('h2:has-text("Background and Needs Assessment")')).to_be_visible(timeout=120000)
   # Take screenshot  
    page.screenshot(path="playwright/test-results/5_proposal_created.png")