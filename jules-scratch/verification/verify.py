from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Login
    page.goto("http://localhost:8503/login")
    page.get_by_label("Email").fill("user1@example.com")
    page.get_by_label("Password").fill("password")
    page.screenshot(path="jules-scratch/verification/login_before_click.png")
    page.get_by_role("button", name="LOGIN").click(timeout=60000)
    page.wait_for_url("http://localhost:8503/dashboard")

    # Dashboard screenshot
    page.click('button[aria-label="Options"]')
    page.screenshot(path="jules-scratch/verification/dashboard.png")

    # Navigate to approved proposal
    page.get_by_text("Child Protection Ukraine").click()
    page.wait_for_url("http://localhost:8503/chat")

    # Chat page screenshot
    page.screenshot(path="jules-scratch/verification/chat_approved.png")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
