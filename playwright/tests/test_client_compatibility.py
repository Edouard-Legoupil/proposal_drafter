from playwright.sync_api import expect


def test_client_compatibility_warning(page, login_user):
    """Test that compatibility warning appears for unsupported browsers"""
    # This test would need to mock the user agent or use browser contexts
    # For now, we'll test that the modal can be dismissed

    # Login first
    login_user(page)

    # Check if compatibility modal appears (may not appear if browser is supported)
    modal = page.locator('div[role="dialog"]:has-text("Unsupported Browser")')

    if modal.is_visible():
        # If modal appears, test dismissal
        page.click('button:has-text("Continue Anyway")')
        expect(modal).not_to_be_visible()

        # Verify we can proceed to dashboard
        expect(page).to_have_url("/dashboard")
    else:
        # If no modal, just verify we're on dashboard
        expect(page).to_have_url("/dashboard")


def test_client_compatibility_manual_trigger(page, login_user, mock_user_agent):
    """Test compatibility detection with mocked user agent"""
    # Set a known unsupported user agent
    mock_user_agent(
        page, "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.0.0 Safari/537.36"
    )

    # Login
    login_user(page)

    # Check for compatibility warning
    expect(page.locator("text=Unsupported Browser/OS Detected")).to_be_visible()
    expect(page.locator("text=Windows 7")).to_be_visible()
    expect(page.locator("text=Chrome 90")).to_be_visible()

    # Dismiss warning
    page.click('button:has-text("Continue Anyway")')
    expect(page.locator("text=Unsupported Browser/OS Detected")).not_to_be_visible()
