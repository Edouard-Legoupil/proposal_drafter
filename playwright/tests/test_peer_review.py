import re
from playwright.sync_api import Page, expect

def test_peer_review_flow(page: Page):
    """
    Tests the full peer review flow:
    1. User 1 creates a proposal and submits it for peer review to User 2.
    2. User 2 logs in, submits a review, and completes the process.
    This test assumes 'user1@example.com' and 'user2@example.com' exist.
    """
    base_url = "http://localhost:8502"

    # --- Part 1: User 1 submits for review ---

    # Login as User 1
    page.goto(f"{base_url}/login")
    page.get_by_label("Email").fill("user1@example.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="LOGIN").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Create a new proposal
    page.get_by_role('button', name='Generate New Proposal').click()
    expect(page).to_have_url(re.compile(".*chat"))
    page.get_by_label('Project Title').fill('Peer Review Test Project')
    page.get_by_label('Targeted Donor').select_option(label='UNHCR')
    page.get_by_label('Project Duration (in months)').fill('12')
    page.get_by_label('Project Budget (in USD)').fill('100000')
    page.get_by_label('Project Description').fill('This is a test project for peer review.')
    page.get_by_role('button', name='Generate').click()
    # The timeout is increased here as generating a proposal can be slow.
    expect(page.locator('h2:has-text("Executive Summary")')).to_be_visible(timeout=120000)

    # Get the proposal ID from the URL
    url = page.url
    proposal_id = url.split('/')[-1]
    expect(proposal_id).not_to_be_empty()

    # Submit for peer review
    page.get_by_role('button', name='Peer Review').click()

    # This selector is based on a class name and might be brittle.
    page.locator('.multi-select-modal').wait_for()
    # Assuming 'User 2' is the display name for 'user2@example.com'
    page.get_by_text('User 2').click()
    page.get_by_role('button', name='Confirm').click()

    # The status badge selector might need adjustment.
    expect(page.locator('.status-badge.active')).to_have_text('Peer Review')

    # Logout as User 1
    page.get_by_role('button', name='Logout').click()
    expect(page).to_have_url(re.compile(".*login"))

    # --- Part 2: User 2 submits the review ---

    # Login as User 2
    page.get_by_label("Email").fill("user2@example.com")
    page.get_by_label("Password").fill("password") # Assuming same password for simplicity
    page.get_by_role("button", name="LOGIN").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Navigate to the review page
    page.goto(f"{base_url}/review/{proposal_id}")
    expect(page).to_have_url(re.compile(f".*review/{proposal_id}"))

    # Fill in the review and submit
    page.locator('textarea').first.fill('This is a test review comment from User 2.')
    page.get_by_role('button', name='Review Completed').click()

    # Expect to be redirected to the dashboard
    expect(page).to_have_url(re.compile(".*dashboard"))
    expect(page.get_by_role('heading', name='Proposals Dashboard')).to_be_visible()
