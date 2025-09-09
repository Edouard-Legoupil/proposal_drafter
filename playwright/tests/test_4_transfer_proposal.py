import re
import pytest
from playwright.sync_api import Page, expect



def test_user_registration_and_login(page: Page):
    """
    Tests that a new second user can register and then log in.
    """
    # Generate a unique email for the new user
    email = "testuser2@unhcr.org"
    password = "password123"
    name = "Test User"

    # Base URL for the application
    base_url = "http://localhost:8502"


    # Take screenshot landinf 
    page.screenshot(path="playwright/test-results/0_landing.png")

    # Navigate to the registration page
    # Assuming the registration page is at /register
    page.goto(f"{base_url}/register")

    # Fill out the registration form
    # These are common labels, but might need adjustment
    page.get_by_label("Name").fill(name)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    # Select a team, security question and answer
    page.get_by_label("Team").select_option(index=1)
    page.get_by_label("Security Question").select_option(label="Favourite animal?")
    page.get_by_label("Answer").fill("Dog")

    # Create test-results directory if it doesn't exist
    os.makedirs("playwright/test-results", exist_ok=True)
    
    # Take screenshot before clicking register
    page.screenshot(path="playwright/test-results/2_register_page_before_submit.png")

    # Click the register button
    # Assuming the button has the text "Register"
    page.get_by_role("button", name="Register").click()



    # Expect to be redirected to the dashboard
    expect(page).to_have_url(re.compile(".*dashboard"))
    # The dashboard heading might be different
    expect(page.get_by_text("Draft Smart Project Proposals with AI, Curated Knowledge and Peer Review.")).to_be_visible()

    # Take screenshot after clicking register
    page.screenshot(path="playwright/test-results/3_register_page_after_submit.png")

    # Click the user menu to reveal the logout button, then click logout
    page.locator("button[popovertarget='ID_Chat_logoutPopover']").click()
    page.get_by_text("Logout").click()



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

def test_dashboard_displays_project_options_popover(page: Page):
    """
    Tests that the project options popover is displayed on the dashboard.
    """
    expect(page.get_by_text('Test Project from Playwright')).to_be_visible()
    # This selector is based on a class name and might be brittle.
    page.locator('.Dashboard_project_tripleDotsContainer').first.click()
    expect(page.get_by_text('View')).to_be_visible()
    expect(page.get_by_text('Delete')).to_be_visible()
    expect(page.get_by_text('Transfer')).to_be_visible()





