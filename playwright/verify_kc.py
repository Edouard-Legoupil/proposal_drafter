from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Login
    page.goto("http://localhost:8502/login")
    page.get_by_label("Email").fill("user1@example.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="LOGIN").click()
    page.wait_for_url("http://localhost:8502/dashboard")

    # Make sure we are on the dashboard
    expect(page.get_by_role("button", name="My Proposals")).to_be_visible()

    # Switch to knowledge card tab
    page.get_by_role("tab", name="Knowledge Card").click()

    # Screenshot of the dashboard with knowledge cards
    page.screenshot(path="playwright/kc_dashboard.png")

    # Navigate to create new knowledge card
    page.get_by_role("button", name="Create New Knowledge Card").click()
    expect(page.get_by_role("heading", name="Create New Knowledge Card")).to_be_visible()

    # Screenshot of the new form layout
    page.screenshot(path="playwright/kc_form_layout.png")

    # Test filtering
    page.get_by_label("Link To").select_option("field_context")
    page.get_by_label("Geographic Coverage").select_option("One Country Operation")

    # Screenshot of the filtered dropdown
    page.screenshot(path="playwright/kc_form_filtered.png")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
