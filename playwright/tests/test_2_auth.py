import re
import uuid
from playwright.sync_api import Page, expect

def test_existing_user_login_and_logout(page: Page):
    """
    Tests that an existing user can log in and log out.
    This test assumes a user with the specified credentials already exists.
    """
    email = "user1@example.com"
    password = "password"
    base_url = "http://localhost:8502"

    # Navigate to the login page
    page.goto(f"{base_url}/login")

    # Fill in the login form
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="LOGIN").click()

    # Expect to be redirected to the dashboard
    expect(page).to_have_url(re.compile(".*dashboard"))
    expect(page.get_by_role("heading", name="Proposals Dashboard")).to_be_visible()

    # Click the logout button
    page.get_by_role("button", name="Logout").click()

    # Expect to be back on the login page
    expect(page).to_have_url(re.compile(".*login"))
