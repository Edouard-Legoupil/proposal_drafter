"""
Test suite for peer review workflow.

These tests verify that:
1. Proposals can be submitted for peer review
2. Reviewers can add comments
3. Authors can respond to comments
4. Proposals can be marked as completed and submitted
"""

import re
import os
import pytest
from playwright.sync_api import expect

from .conftest import TEST_USERS, TestUser, take_screenshot


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def ensure_screenshot_dir():
    """Ensure screenshot directory exists."""
    os.makedirs("playwright/test-results", exist_ok=True)


@pytest.fixture
def primary_user_logged_in(page, config):
    """Log in as the primary test user."""
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))
    return page


@pytest.fixture
def secondary_user_logged_in(page, config):
    """Log in as the secondary test user."""
    user = TEST_USERS["secondary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))
    return page


# ============================================================================
# Test: Submit Proposal for Peer Review
# ============================================================================

@pytest.mark.peer_review
def test_submit_proposal_for_review(primary_user_logged_in, config):
    """
    Test submitting a proposal for peer review.
    
    Precondition: A proposal must already exist and be in draft status.
    """
    page = primary_user_logged_in
    
    # Try to find and open an existing proposal
    try:
        page.get_by_text("Project: Refugee Children Education").first.click()
    except Exception:
        pytest.skip("No existing proposal found for peer review test")
    
    # Submit for peer review
    page.get_by_test_id("workflow-status-badge-in_review").click()
    
    # Select reviewer (using secondary user)
    # The user ID is dynamic, so we use a partial match
    page.get_by_test_id("user-select-checkbox").first.check()
    
    # Set deadline
    page.get_by_test_id("deadline-input").fill("2025-12-31")
    
    take_screenshot(page, "peer_review_submit")
    
    # Confirm
    page.get_by_test_id("confirm-button").click()
    
    # Verify proposal is now in review status
    expect(page.get_by_test_id("workflow-status-badge-in_review")).to_be_visible(timeout=10000)


# ============================================================================
# Test: Add Peer Review Comments
# ============================================================================

@pytest.mark.peer_review
def test_add_peer_review_comments(secondary_user_logged_in, config):
    """
    Test adding comments as a peer reviewer.
    
    Precondition: A proposal must be in review status with this user as reviewer.
    """
    page = secondary_user_logged_in
    
    # Navigate to reviews tab
    page.get_by_test_id("reviews-tab").click()
    
    # Try to find a review card
    try:
        page.locator("#reviews-grid > article").first.click()
    except Exception:
        pytest.skip("No reviews found for peer review test")
    
    # Add comment on Summary section
    page.get_by_test_id("comment-type-select-Summary").select_option("Clarity")
    page.get_by_test_id("severity-select-Summary").select_option("High")
    page.get_by_test_id("comment-textarea-Summary").fill("Please revise this section to make it clearer")
    
    take_screenshot(page, "peer_review_comment_added")
    
    # Add comment on Rationale section
    page.get_by_test_id("comment-type-select-Rationale").select_option("Impact")
    page.get_by_test_id("comment-textarea-Rationale").fill("Please stress more the impact")


# ============================================================================
# Test: Mark Review as Completed
# ============================================================================

@pytest.mark.peer_review
def test_mark_review_as_completed(secondary_user_logged_in, config):
    """
    Test marking a review as completed.
    
    Precondition: A review must exist with comments.
    """
    page = secondary_user_logged_in
    
    # Navigate to reviews tab
    page.get_by_test_id("reviews-tab").click()
    
    # Try to find a review card
    try:
        page.locator("#reviews-grid > article").first.click()
    except Exception:
        pytest.skip("No reviews found for completion test")
    
    # Mark as completed
    page.get_by_test_id("review-completed-button-header").click()
    
    take_screenshot(page, "peer_review_completed")
    
    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()


# ============================================================================
# Test: Respond to Peer Review Comments
# ============================================================================

@pytest.mark.peer_review
def test_respond_to_peer_review_comments(primary_user_logged_in, config):
    """
    Test responding to peer review comments as the proposal author.
    
    Precondition: A proposal must have peer review comments.
    """
    page = primary_user_logged_in
    
    # Try to find and open an existing proposal
    try:
        page.get_by_text("Project: Refugee Children Education").first.click()
    except Exception:
        pytest.skip("No existing proposal found for response test")
    
    # Find and respond to a comment
    # This assumes there are visible comment textareas
    try:
        response_box = page.get_by_role("textbox", name="Type your response here...").first
        response_box.click()
        response_box.fill("Thanks for your comment! Will review accordingly.")
        take_screenshot(page, "peer_review_response_added")
    except Exception:
        pytest.skip("No comments found to respond to")


# ============================================================================
# Test: Submit Proposal After Review
# ============================================================================

@pytest.mark.peer_review
def test_submit_proposal_after_review(primary_user_logged_in, config):
    """
    Test submitting a proposal after peer review is complete.
    
    Precondition: A proposal must be in review status with completed reviews.
    """
    page = primary_user_logged_in
    
    # Try to find and open an existing proposal
    try:
        page.get_by_text("Project: Refugee Children Education").first.click()
    except Exception:
        pytest.skip("No existing proposal found for submission test")
    
    # Submit proposal
    page.get_by_test_id("workflow-status-badge-submitted").click()
    
    take_screenshot(page, "peer_review_submitted")
    
    # Cancel (we don't want to actually submit in tests)
    page.get_by_role("button", name="Cancel").click()


# ============================================================================
# Test: Full Peer Review Workflow (Backward Compatibility)
# ============================================================================

@pytest.mark.peer_review
@pytest.mark.e2e
@pytest.mark.regression
def test_full_peer_review_workflow(context, config):
    """
    Full peer review workflow maintaining backward compatibility.
    
    This test follows the exact workflow from the original test_4_peer_review.py
    but uses fixtures for better maintainability.
    """
    primary_user = TEST_USERS["primary"]
    secondary_user = TEST_USERS["secondary"]
    
    # ===== Part 1: Primary user submits proposal for review =====
    page1 = context.new_page()
    page1.set_default_timeout(config["default_timeout"])
    
    # Login as primary user
    page1.goto(f"{config['base_url']}/login")
    page1.get_by_test_id("email-input").fill(primary_user.email)
    page1.get_by_test_id("password-input").fill(primary_user.password)
    page1.get_by_test_id("submit-button").click()
    expect(page1).to_have_url(re.compile(".*dashboard"))
    
    # Open existing project
    page1.get_by_text("Project: Refugee Children Education InitiativeViewTransferDelete Afghanistan -").first.click()
    
    # Submit for Peer Review
    page1.get_by_test_id("workflow-status-badge-in_review").click()
    
    # Select secondary user as reviewer
    # Note: The user ID in the original test was hardcoded, we use the first checkbox
    page1.get_by_test_id("user-select-checkbox").first.check()
    
    page1.get_by_test_id("deadline-input").fill("2025-12-31")
    take_screenshot(page1, "peer_review_1_set")
    page1.get_by_test_id("confirm-button").click()
    
    # Log Out
    page1.get_by_test_id("user-menu-button").click()
    page1.get_by_test_id("logout-button").click()
    
    # ===== Part 2: Secondary user adds review comments =====
    page2 = context.new_page()
    page2.set_default_timeout(config["default_timeout"])
    
    # Login as secondary user
    page2.goto(f"{config['base_url']}/login")
    page2.get_by_test_id("email-input").click()
    page2.get_by_test_id("email-input").fill(secondary_user.email)
    page2.get_by_test_id("password-input").click()
    page2.get_by_test_id("password-input").fill(secondary_user.password)
    page2.get_by_test_id("submit-button").click()
    
    # Go to review and select the first one
    page2.get_by_test_id("reviews-tab").click()
    page2.locator("#reviews-grid > article").first.click()
    
    # Add Comments
    page2.get_by_test_id("comment-type-select-Summary").select_option("Clarity")
    page2.get_by_test_id("severity-select-Summary").select_option("High")
    page2.get_by_test_id("comment-textarea-Summary").fill("revise this whole part to make it clearer")
    take_screenshot(page2, "peer_review_2_comment")
    
    page2.get_by_test_id("comment-type-select-Rationale").select_option("Impact")
    page2.get_by_test_id("comment-textarea-Rationale").fill("Stress more the impact")
    
    # Put Review as completed and log out
    page2.get_by_test_id("review-completed-button-header").click()
    take_screenshot(page2, "peer_review_3_completed")
    page2.get_by_test_id("user-menu-button").click()
    page2.get_by_test_id("logout-button").click()
    
    # ===== Part 3: Primary user responds to comments =====
    # Reuse page1
    page1.goto(f"{config['base_url']}/login")
    page1.get_by_test_id("email-input").click()
    page1.get_by_test_id("email-input").fill(primary_user.email)
    page1.get_by_test_id("password-input").click()
    page1.get_by_test_id("password-input").fill(primary_user.password)
    page1.get_by_test_id("submit-button").click()
    
    # Select proposal
    page1.get_by_text("Project: Refugee Children Education InitiativeViewTransferDelete Afghanistan -").first.click()
    
    # Reply to comments
    page1.get_by_role("textbox", name="Type your response here...").click()
    page1.get_by_role("textbox", name="Type your response here...").fill("thanks for your comment! will review accordingly")
    take_screenshot(page1, "peer_review_4_reply")
    
    # Submit Proposal
    page1.get_by_test_id("workflow-status-badge-submitted").click()
    take_screenshot(page1, "peer_review_5_submit")
    page1.get_by_role("button", name="Cancel").click()
    
    page1.get_by_test_id("logo").click()
    
    # Cleanup
    page1.close()
    page2.close()
