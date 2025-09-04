import re
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(autouse=True)
def login(page: Page):
    """
    Fixture to log in before each test in this module.
    """
    email = "user1@example.com"
    password = "password"
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

@pytest.mark.skip(reason="This test depends on the successful creation of a proposal in another test, which is not a best practice. It should be refactored to create its own test data.")
def test_edit_and_save_proposal(page: Page):
    """
    Tests that a user can edit and save a proposal.
    NOTE: This test is not independent and depends on a proposal existing on the dashboard.
    """
    # Click on the first proposal in the list
    # This selector is based on a class name and might be brittle.
    page.locator('.proposal-card').first.click()
    expect(page).to_have_url(re.compile(r'\/chat\/.+'))

    # Edit the executive summary
    # This selector is quite specific and might need adjustment.
    executive_summary_editor = page.locator('div[data-testid="section-Executive Summary"] >> .tiptap')
    executive_summary_editor.click()
    edited_text = 'This is an edited executive summary from a Playwright test.'
    executive_summary_editor.fill(edited_text)

    # Click the save button
    page.get_by_role('button', name='Save').click()

    # Reload the page to ensure the change was persisted
    page.reload()
    expect(page).to_have_url(re.compile(r'\/chat\/.+'))

    # Verify the changes have been saved
    expect(executive_summary_editor).to_have_text(edited_text)

@pytest.mark.skip(reason="This test depends on a proposal existing and the download functionality was commented out in the original test.")
def test_download_proposal(page: Page):
    """
    Tests that a user can download a proposal.
    NOTE: This test is not independent and depends on a proposal existing on the dashboard.
    The download logic was commented out in the original JS test.
    """
    # Click on the first proposal in the list
    page.locator('.proposal-card').first.click()
    expect(page).to_have_url(re.compile(r'\/chat\/.+'))

    # Click the download button
    page.get_by_role('button', name='Download').click()

    # Start waiting for the download
    with page.expect_download() as download_info:
        # Click the PDF download button. This part was commented out in the original test.
        # page.get_by_role('button', { name: 'PDF' }).click()
        pass # The user needs to provide the action that triggers the download

    # download = download_info.value
    # expect(download.suggested_filename).to_contain('.pdf')
