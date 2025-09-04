import re
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(autouse=True)
def login(page: Page):
    """
    Fixture to log in before each test in this module.
    """
    email = "testuser@unhcr.org"
    password = "password123"
    base_url = "http://localhost:8502"

    page.goto(f"{base_url}/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="LOGIN").click()
    expect(page).to_have_url(re.compile(".*dashboard"))
    yield

def test_generate_new_proposal(page: Page):
    """
    Tests that a user can generate a new proposal.
    """
    page.get_by_role('button', name='Generate New Proposal').click()
    expect(page).to_have_url(re.compile(".*chat"))

    # Take screenshot before creating Proposal
    page.screenshot(path="playwright/test-results/4_create_proposal.png")
    # Fill in the proposal form
    page.get_by_label('Project Title').fill('Test Project from Playwright')
    page.get_by_label('Targeted Donor').select_option(label='UNHCR')
    page.get_by_label('Project Duration (in months)').fill('12')
    page.get_by_label('Project Budget (in USD)').fill('100000')
    page.get_by_label('Project Description').fill('This is a test project description from a Playwright test.')

    # Click the "Generate" button
    page.get_by_role('button', name='Generate').click()

    # Wait for the sections to be generated. This can be slow.
    expect(page.locator('h2:has-text("Executive Summary")')).to_be_visible(timeout=120000)
    expect(page.locator('h2:has-text("Background and Needs Assessment")')).to_be_visible(timeout=120000)

    # Take screenshot before creating Proposal
    page.screenshot(path="playwright/test-results/5_proposal_created.png")

   # Click the user menu to reveal the logout button, then click logout
    page.locator("button[popovertarget='ID_Chat_logoutPopover']").click()
    page.get_by_text("Logout").click()
