import re
from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Sign up a new user
    page.goto("http://localhost:8503/register")
    page.screenshot(path="jules-scratch/verification/register_page.png")
    page.get_by_label("Name").fill("testuser")
    page.get_by_label("Email").fill("testuser@example.com")
    page.get_by_label("Password").fill("password")
    page.wait_for_selector('select[data-testid="team-select"] option:not([value=""])')
    page.get_by_label("Team").select_option(label="DRRM")
    page.get_by_label("Security Question").select_option("What is your mother's maiden name?")
    page.get_by_label("Security Answer").fill("test")
    page.get_by_role("button", name="Register").click()

    # Log in with the new user
    page.goto("http://localhost:8503/login")
    page.get_by_label("Email").fill("testuser@example.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click()

    # Verify login was successful
    expect(page).to_have_url("http://localhost:8503/dashboard")
    page.screenshot(path="jules-scratch/verification/login_verification.png")

    # Navigate to knowledge card creation
    page.goto("http://localhost:8503/knowledge-card")

    # Fill out the form
    page.get_by_label("Link To").select_option("donor")
    page.get_by_label("Title*").fill("Test Knowledge Card for SSE")
    page.get_by_label("Description").fill("This is a test to verify SSE functionality.")

    # Add a reference
    page.get_by_role("button", name="Add Reference").click()
    page.get_by_label("Reference Type*").select_option("Donor Content")
    page.get_by_placeholder("https://example.com").fill("https://www.unhcr.org/what-we-do")

    # Click the populate button
    page.get_by_role("button", name="Populate Card Content").click()

    # Wait for the progress modal to appear and take a screenshot
    expect(page.get_by_role("heading", name="Generating Content")).to_be_visible()
    page.screenshot(path="jules-scratch/verification/verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
