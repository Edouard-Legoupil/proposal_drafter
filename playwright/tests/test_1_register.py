import re
import uuid
from playwright.sync_api import Page, expect

def test_user_registration_and_login(page: Page):
    """
    Tests that a new user can register and then log in.
    """
    # Generate a unique email for the new user
    unique_id = uuid.uuid4().hex[:8]
    email = f"testuser_{unique_id}@example.com"
    password = "password123"
    name = "Test User"

    # Base URL for the application
    base_url = "http://localhost:8502"

    # Navigate to the registration page
    # Assuming the registration page is at /register
    page.goto(f"{base_url}/register")

    # Fill out the registration form
    # These are common labels, but might need adjustment
    page.get_by_label("Name").fill(name)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)

    # Click the register button
    # Assuming the button has the text "Register"
    page.get_by_role("button", name="Register").click()

    # Expect to be redirected to the login page
    expect(page).to_have_url(re.compile(".*login"))
    expect(page.get_by_role("heading", name="Login")).to_be_visible()

    # Now, log in with the new user
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="LOGIN").click()

    # Expect to be redirected to the dashboard
    expect(page).to_have_url(re.compile(".*dashboard"))
    # The dashboard heading might be different
    expect(page.get_by_role("heading", name="Proposals Dashboard")).to_be_visible()

    # Click the logout button to clean up the session
    # The logout button might have a different name or be in a menu
    page.get_by_role("button", name="Logout").click()

    # Expect to be back on the login page
    expect(page).to_have_url(re.compile(".*login"))


