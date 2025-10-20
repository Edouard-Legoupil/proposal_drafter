import re
import pytest
from playwright.sync_api import Page, expect

def test_edit_and_save_proposal(page: Page):
    """
    Tests that a user can edit and save a proposal.
    NOTE: This test is not independent and depends on a proposal existing on the dashboard.
    """
    email = "testuser@unhcr.org"
    password = "password123"
    base_url = "http://localhost:8502"

    page.goto(f"{base_url}/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="LOGIN").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

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

   # Take screenshot 
    page.screenshot(path="playwright/test-results/6_edit_section.png")
    
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

def test_chat_displays_updated_workflow_badges(page: Page):
    """
    Tests that the updated workflow badges are displayed on the chat page.
    """
    page.get_by_text('Child Protection Ukraine').click()
    expect(page).to_have_url(re.compile(".*chat"))
    expect(page.get_by_text('Workflow Stage')).to_be_visible()
    expect(page.get_by_text('Pre-Submission')).to_be_visible()
    expect(page.get_by_title('Initial drafting stage - Author + AI')).to_be_visible()

def test_chat_displays_revert_buttons_for_past_statuses(page: Page):
    """
    Tests that revert buttons for past statuses are displayed on the chat page.
    """
    page.get_by_text('Child Protection Ukraine').click()
    expect(page).to_have_url(re.compile(".*chat"))
    expect(page.get_by_role('button', name='Revert')).to_be_visible()

def test_chat_displays_pre_submission_review_comments(page: Page):
    """
    Tests that pre-submission review comments are displayed on the chat page.
    """
    page.get_by_text('Test Project from Playwright').click()
    expect(page).to_have_url(re.compile(".*chat"))
    expect(page.get_by_text('Peer Reviews')).to_be_visible()
    expect(page.get_by_text('Bob:')).to_be_visible()
    expect(page.get_by_placeholder('Respond to this review...')).to_be_visible()

def test_chat_displays_upload_button_for_approved_proposals(page: Page):
    """
    Tests that the upload button for approved proposals is displayed on the chat page.
    """
    page.get_by_text('Child Protection Ukraine').click()
    expect(page).to_have_url(re.compile(".*chat"))
    expect(page.get_by_label('Upload Approved Document')).to_be_visible()