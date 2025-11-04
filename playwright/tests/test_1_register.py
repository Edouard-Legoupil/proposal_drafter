import re
from playwright.sync_api import Page, expect
import os

def test_user_registration(page: Page):
    """
    Tests that a new user can register and then log in.
    """
    base_url = "http://localhost:8503"

    # Mock the API calls
    page.route(f"{base_url}/api/teams", lambda route: route.fulfill(json={"teams": [{"id": "1", "name": "Test Team"}]}))
    page.route(f"{base_url}/api/sso-status", lambda route: route.fulfill(json={"enabled": False}))
    page.route(f"{base_url}/api/signup", lambda route: route.fulfill(status=200))
    page.route(f"{base_url}/api/login", lambda route: route.fulfill(status=200))


    # Generate a unique email for the new user
    email = "test_user@unhcr.org"
    password = "password123"
    name = "Test User"

    page.goto(base_url)

    # Create test-results directory if it doesn't exist
    os.makedirs("playwright/test-results", exist_ok=True)

    # Take screenshot landing
    page.screenshot(path="playwright/test-results/register_landing.png")

    # Navigate to the registration page
    page.get_by_test_id("register-link").click()

    # Fill out the registration form
    page.get_by_label("Name").fill(name)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    # Select a team, security question and answer
    page.get_by_label("Team").select_option(index=1)
    page.get_by_label("Security Question").select_option(label="Favourite animal?")
    page.get_by_label("Answer").fill("Dog")
    page.get_by_test_id("acknowledgement-checkbox").check()

    # Take screenshot before clicking register
    page.screenshot(path="playwright/test-results/register_page_before_submit.png")

    # Click the register button
    page.get_by_role("button", name="Register").click()

    # Expect to be redirected to the dashboard
    expect(page).to_have_url(re.compile(".*dashboard"))
    expect(page.get_by_text("Draft Smart Project Proposals with AI, Curated Knowledge and Peer Review.")).to_be_visible()

    # Take screenshot after clicking register
    page.screenshot(path="playwright/test-results/register_page_after_submit.png")

    # Click the user menu to reveal the logout button, then click logout
    page.locator("button[popovertarget='ID_Chat_logoutPopover']").click()
    page.get_by_text("Logout").click()

    # Expect to be back on the login page
    expect(page).to_have_url(re.compile(".*login"))

    # Now, log in with the new user
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="LOGIN").click()

    # Expect to be redirected to the dashboard
    expect(page).to_have_url(re.compile(".*dashboard"))
