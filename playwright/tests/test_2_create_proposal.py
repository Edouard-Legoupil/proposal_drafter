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
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="LOGIN").click()

    expect(page).to_have_url(re.compile(".*dashboard"))
    
    page.get_by_role('button', name='Start a new proposal').click()
    
    expect(page).to_have_url(re.compile(".*chat"))

   # Take screenshot 
    page.screenshot(path="playwright/test-results/4_generate_proposal.png")


    # Fill in the proposal form
    page.get_by_label('Project Draft Short name').fill('Refugee Children Education Initiative - Kenya')
    page.get_by_placeholder('Provide as much details as possible on your initial project idea!').fill('Establishing a comprehensive primary education program for 2,500 refugee children aged 6-14 in Kakuma Refugee Camp, Kenya. The project will construct 15 semi-permanent classrooms, train 45 local teachers and refugee volunteers in child-centered pedagogy, develop culturally appropriate learning materials in multiple languages (English, Swahili, Arabic, and local languages), and establish a school feeding program to improve attendance. Key activities include teacher certification workshops, procurement of educational supplies and furniture, community engagement sessions with refugee parents, and establishing referral pathways for children with special needs. The program will follow Kenya national curriculum while incorporating psychosocial support elements to address trauma and displacement challenges.')

    # Main Outcome (multiselect)

    page.locator(".css-19bb58m").first.click()
    page.get_by_role("option", name="OA11-Education").click()
    page.locator(".css-19bb58m").first.click()
    page.get_by_role("option", name="OA7-Community").click()

    #page.locator('div').filter(has_text=re.compile(r'^\*Main Outcome$')).locator('div').nth(1).click()
    #page.get_by_text('Outcome 1', exact=True).click()

    page.get_by_label('Beneficiaries Profile').fill('Refugee Kids')    
   # page.get_by_role("textbox", name="Beneficiaries Profile*").click()
   # page.get_by_role("textbox", name="Beneficiaries Profile*").fill("Refugee Children")
    
    page.get_by_label('Potential Implementing Partner').fill('UNHCR, UNICEF, Save the Children')
    # page.get_by_role("textbox", name="Potential Implementing Partner").fill("UNHCR, UNICEF")

    # Geographical Scope (select)  -------
    page.get_by_label('Geographical Scope').select_option(label='One Country Operation')

    # Country / Location(s) (creatable select)  -------
   # page.locator('div').filter(has_text=re.compile(r'^\*Country / Location\(s\)$')).locator('div').nth(1).click()
   # page.get_by_text('Country 1', exact=True).click()
    page.locator(".css-hlgwow > .css-19bb58m").first.click()
    page.get_by_role("option", name="Kenya").click()


    # Budget Range (creatable select) -------
    #page.locator('div').filter(has_text=re.compile(r'^\*Budget Range$')).#locator('div').nth(1).click()
    #page.get_by_text('100k$').click()
    page.locator(".css-13cymwt-control > .css-hlgwow > .css-19bb58m").first.click()
    page.get_by_role("option", name="2M$").click()

    # Duration (creatable select)  -------
    #page.locator('div').filter(has_text=re.compile(r'^\*Duration$')).locator('div').nth(1).click()
    #page.get_by_text('6 months', exact=True).click()
    page.locator("div:nth-child(3) > div:nth-child(3) > .css-b62m3t-container > .css-13cymwt-control > .css-hlgwow > .css-19bb58m").click()
    page.get_by_role("option", name="12 months", exact=True).click()

    # Targeted Donor (creatable select)  -------
    #page.locator('div').filter(has_text=re.compile(r'^\*Targeted Donor$')).locator('div').nth(1).click()
    #page.get_by_text('UNHCR', exact=True).click()
    page.locator("div:nth-child(4) > .css-b62m3t-container > .css-13cymwt-control > .css-hlgwow > .css-19bb58m").click()
    page.get_by_role("option", name="United States of America -").click()
    
    # Click the "Generate" button  -------
    page.get_by_role('button', name='Generate').click()

    # Wait for the sections to be generated. This can be slow.  -------
    #expect(page.locator('h2:has-text("Executive Summary")')).to_be_visible(timeout=120000)

    #expect(page.locator('h2:has-text("Background and Needs Assessment")')).to_be_visible(timeout=120000)
   # Take screenshot  
    page.screenshot(path="playwright/test-results/5_proposal_created.png")

    browser.close()