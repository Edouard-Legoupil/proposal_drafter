from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to the knowledge card
    page.goto("http://localhost:8507/knowledge-card/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")

    # Add a new reference
    page.get_by_test_id("add-reference-button").click()
    page.wait_for_timeout(500)
    page.get_by_placeholder("https://example.com").fill("https://www.google.com")
    page.locator('select').nth(1).select_option('Social Media')
    page.locator(".kc-reference-edit-actions > button:first-child").click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("https://www.google.com")).to_be_visible(timeout=10000)

    # Edit the new reference
    page.get_by_role("button").nth(5).click()
    page.wait_for_timeout(500)
    page.get_by_placeholder("https://example.com").fill("https://www.unhcr.org/social")
    page.locator(".kc-reference-edit-actions > button:first-child").click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("https://www.unhcr.org/social")).to_be_visible(timeout=10000)

    # Delete a reference
    page.get_by_role("button").nth(6).click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("https://www.unhcr.org/social")).not_to_be_visible(timeout=10000)

    # View history
    page.get_by_role("button", name="View Content History").click()
    expect(page.get_by_text("Knowledge Card History")).to_be_visible()

    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/knowledge_card_redesign.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
