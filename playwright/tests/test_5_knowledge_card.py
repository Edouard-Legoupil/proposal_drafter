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
    # No teardown needed for this fixture, session is ended by browser context closing

def test_create_new_knowledge_card(page: Page):
    """
    Tests that a user can create a new knowledge card.
    """
    base_url = "http://localhost:8502"
    page.goto(f"{base_url}/knowledge-card/new")

    # Expect the page to have the correct heading
    expect(page.get_by_role("heading", name="Create New Knowledge Card")).to_be_visible()

    # Fill in the form
    page.get_by_label('Link To').select_option(label='Donor')

    # The react-select component can be tricky. These selectors are based on the JS test.
    # They might need to be adjusted if they are not stable.
    # The #react-select-2-input is particularly brittle.
    page.locator('.react-select__control').click()
    # A more robust selector would be to target the input based on the control's id
    # but for now we will stick to the original test's locator.
    page.locator('input[id^="react-select-"]').fill('New Donor')
    page.get_by_text('Create "New Donor"').click()

    page.get_by_label('Title*').fill('Test Knowledge Card from Playwright')
    page.get_by_label('Description').fill('This is a test knowledge card created by a Playwright test.')
    page.get_by_placeholder('https://example.com').fill('https://www.unhcr.org')
    page.get_by_placeholder('Reference Type').fill('Test Reference')

    # Set up a handler for the dialog that is expected to appear
    page.on('dialog', lambda dialog: dialog.accept())

    # Click the save button
    page.get_by_role('button', name='Save Card').click()

    # After saving, the user should be redirected to the knowledge card list
    expect(page).to_have_url(re.compile(".*knowledge-cards"))
    expect(page.get_by_text("Test Knowledge Card from Playwright")).to_be_visible()

def test_knowledge_card_has_updated_form_layout(page: Page):
    """
    Tests that the knowledge card form has the updated layout.
    """
    page.get_by_role('tab', name='Knowledge Card').click()
    page.get_by_role('button', name='Create New Knowledge Card').click()
    expect(page.get_by_label('Reference Type*')).to_be_visible()
    # This selector is based on a class name and might be brittle.
    expect(page.locator('.squared-btn')).to_be_visible()


def test_knowledge_card_displays_correct_icon_on_dashboard(page: Page):
    """
    Tests that the correct icon is displayed for knowledge cards on the dashboard.
    """
    page.get_by_role('tab', name='Knowledge Card').click()
    # This selector is based on a class name and might be brittle.
    expect(page.locator('.fa-money-bill-wave')).to_be_visible()