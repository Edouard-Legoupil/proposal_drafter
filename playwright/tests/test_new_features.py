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

def test_dashboard_displays_project_options_popover(page: Page):
    """
    Tests that the project options popover is displayed on the dashboard.
    """
    expect(page.get_by_text('Colombia Shelter Project')).to_be_visible()
    # This selector is based on a class name and might be brittle.
    page.locator('.Dashboard_project_tripleDotsContainer').first.click()
    expect(page.get_by_text('View')).to_be_visible()
    expect(page.get_by_text('Delete')).to_be_visible()
    expect(page.get_by_text('Transfer')).to_be_visible()

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
    page.get_by_text('Colombia Shelter Project').click()
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

def test_knowledge_card_displays_correct_icon_on_dashboard(page: Page):
    """
    Tests that the correct icon is displayed for knowledge cards on the dashboard.
    """
    page.get_by_role('tab', name='Knowledge Card').click()
    # This selector is based on a class name and might be brittle.
    expect(page.locator('.fa-money-bill-wave')).to_be_visible()

def test_knowledge_card_has_updated_form_layout(page: Page):
    """
    Tests that the knowledge card form has the updated layout.
    """
    page.get_by_role('tab', name='Knowledge Card').click()
    page.get_by_role('button', name='Create New Knowledge Card').click()
    expect(page.get_by_label('Reference Type*')).to_be_visible()
    # This selector is based on a class name and might be brittle.
    expect(page.locator('.squared-btn')).to_be_visible()
