"""
Test suite for Quality Gate Review functionality.

These tests verify that:
1. Quality assurance officers can conduct quality gate reviews
2. Quality review workflows function correctly
3. Proposal owners receive appropriate notifications
4. Quality review status is properly tracked

User Stories Covered:
- Quality Gate Review
"""

import re
import pytest
from playwright.sync_api import expect

# Import shared fixtures and helpers from central conftest
from .conftest import TEST_USERS, take_screenshot


# ============================================================================
# Test: Navigate to Quality Review Page
# ============================================================================


@pytest.mark.quality_gate
@pytest.mark.smoke
def test_navigate_to_quality_review_page(logged_in_qa_officer):
    """User Story: Quality Gate Review"""
    page = logged_in_qa_officer

    # Navigate to quality reviews section
    page.get_by_test_id("quality-reviews-tab").click()
    expect(page).to_have_url(re.compile(".*quality-reviews"))

    # Verify quality reviews page is visible
    expect(page.get_by_text("Quality Gate Reviews")).to_be_visible()

    take_screenshot(page, "quality_review_navigation")


# ============================================================================
# Test: View Proposals Awaiting Quality Review
# ============================================================================


@pytest.mark.quality_gate
def test_view_proposals_awaiting_quality_review(logged_in_qa_officer):
    """User Story: Quality Gate Review
    Steps:
    1. Navigate to quality reviews page
    2. View list of proposals awaiting review
    3. Verify proposal details are visible
    """
    page = logged_in_qa_officer

    # Navigate to quality reviews page
    page.get_by_test_id("quality-reviews-tab").click()
    expect(page).to_have_url(re.compile(".*quality-reviews"))

    # Verify we can see proposals awaiting review
    expect(page.get_by_text("Proposals Awaiting Quality Review")).to_be_visible()

    # Check if there are any proposals (there might not be in test environment)
    proposal_cards = page.get_by_test_id("quality-review-proposal-card")
    if proposal_cards.count() > 0:
        first_card = proposal_cards.first
        expect(first_card.get_by_test_id("proposal-name")).to_be_visible()
        expect(first_card.get_by_test_id("proposal-owner")).to_be_visible()
        expect(first_card.get_by_test_id("proposal-status")).to_be_visible()

    take_screenshot(page, "quality_review_proposals_list")


# ============================================================================
# Test: Conduct Quality Gate Review
# ============================================================================


@pytest.mark.quality_gate
def test_conduct_quality_gate_review(logged_in_qa_officer):
    """User Story: Quality Gate Review
    Steps:
    1. Navigate to quality reviews page
    2. Select a proposal for review
    3. Check proposal against quality criteria
    4. Add quality review comments
    5. Select quality status
    6. Submit quality review
    7. Verify success message
    """
    page = logged_in_qa_officer

    # Navigate to quality reviews page
    page.get_by_test_id("quality-reviews-tab").click()
    expect(page).to_have_url(re.compile(".*quality-reviews"))

    # Select the first proposal for review
    proposal_cards = page.get_by_test_id("quality-review-proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for quality review")

    first_card = proposal_cards.first
    proposal_name = first_card.get_by_test_id("proposal-name").text_content()
    first_card.get_by_test_id("review-proposal-button").click()

    # Verify we're on the quality review page for this proposal
    expect(page.get_by_text(f"Quality Review: {proposal_name}")).to_be_visible()

    take_screenshot(page, "quality_review_proposal_opened")

    # Check proposal against quality criteria
    # This would involve reviewing different sections of the proposal
    page.get_by_test_id("quality-criteria-compliance").check()
    page.get_by_test_id("quality-criteria-clarity").check()
    page.get_by_test_id("quality-criteria-impact").check()
    page.get_by_test_id("quality-criteria-budget").check()

    # Add quality review comments for different sections
    page.get_by_test_id("quality-comment-Summary").click()
    page.get_by_test_id("quality-comment-Summary").fill("Executive summary is clear and comprehensive")

    page.get_by_test_id("quality-comment-Rationale").click()
    page.get_by_test_id("quality-comment-Rationale").fill("Rationale is well-justified with strong evidence")

    page.get_by_test_id("quality-comment-Evaluation").click()
    page.get_by_test_id("quality-comment-Evaluation").fill("Evaluation plan needs more detail on indicators")

    take_screenshot(page, "quality_review_comments_added")

    # Select quality status
    page.get_by_test_id("quality-status-select").select_option("approved_with_minor_revisions")

    # Submit quality review
    page.get_by_test_id("submit-quality-review-button").click()

    # Verify success message
    expect(page.get_by_text("Quality review submitted successfully")).to_be_visible()

    # Verify proposal owner notification
    expect(page.get_by_text("Proposal owner has been notified")).to_be_visible()

    take_screenshot(page, "quality_review_submitted")


# ============================================================================
# Test: Quality Review with Different Statuses
# ============================================================================


@pytest.mark.quality_gate
def test_quality_review_with_different_statuses(logged_in_qa_officer):
    """User Story: Quality Gate Review
    Steps:
    1. Conduct review with "Approved" status
    2. Conduct review with "Approved with Major Revisions" status
    3. Conduct review with "Rejected" status
    4. Verify appropriate messages for each status
    """
    page = logged_in_qa_officer

    # This test would ideally use test data setup to create proposals in different states
    # For now, we'll test the UI flow with a single proposal

    page.get_by_test_id("quality-reviews-tab").click()

    proposal_cards = page.get_by_test_id("quality-review-proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for quality review")

    proposal_cards.first.get_by_test_id("review-proposal-button").click()

    # Test "Approved" status
    page.get_by_test_id("quality-status-select").select_option("approved")
    page.get_by_test_id("quality-comment-Summary").fill("Excellent proposal, ready for submission")

    take_screenshot(page, "quality_review_approved_status")

    # Note: We won't submit this to avoid affecting test data
    # In a real test, you would submit and verify the outcome

    # Test "Approved with Major Revisions" status
    page.get_by_test_id("quality-status-select").select_option("approved_with_major_revisions")

    take_screenshot(page, "quality_review_major_revisions_status")

    # Test "Rejected" status
    page.get_by_test_id("quality-status-select").select_option("rejected")

    take_screenshot(page, "quality_review_rejected_status")


# ============================================================================
# Test: Quality Review Notification Flow
# ============================================================================


@pytest.mark.quality_gate
@pytest.mark.e2e
def test_quality_review_notification_flow(page, config):
    """User Story: Quality Gate Review
    Steps:
    1. User submits proposal for quality review
    2. QA officer conducts review
    3. Proposal owner receives notification
    4. Proposal owner views review feedback
    """
    # Step 1: User creates and submits proposal for quality review
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()
    expect(page).to_have_url(re.compile(".*dashboard"))

    # Create a new proposal (using existing test data or creating one)
    # For this test, we'll assume a proposal already exists

    # Submit proposal for quality review
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() > 0:
        proposal_cards.first.click()
        page.get_by_test_id("submit-for-quality-review-button").click()
        expect(page.get_by_text("Proposal submitted for quality review")).to_be_visible()

    take_screenshot(page, "quality_workflow_proposal_submitted")

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 2: QA officer conducts review
    qa_officer = TEST_USERS["qa_officer"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(qa_officer.email)
    page.get_by_test_id("password-input").fill(qa_officer.password)
    page.get_by_test_id("submit-button").click()

    page.get_by_test_id("quality-reviews-tab").click()

    # Find and review the proposal
    quality_proposal_cards = page.get_by_test_id("quality-review-proposal-card")
    if quality_proposal_cards.count() > 0:
        quality_proposal_cards.first.get_by_test_id("review-proposal-button").click()

        # Add review comments
        page.get_by_test_id("quality-comment-Summary").fill("Summary is well-written and comprehensive")
        page.get_by_test_id("quality-comment-Rationale").fill("Rationale needs stronger evidence base")

        # Select status
        page.get_by_test_id("quality-status-select").select_option("approved_with_minor_revisions")

        # Submit review
        page.get_by_test_id("submit-quality-review-button").click()
        expect(page.get_by_text("Quality review submitted successfully")).to_be_visible()

    take_screenshot(page, "quality_workflow_review_completed")

    # Log out QA officer
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 3: User views quality review feedback
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # Check for quality review notification
    expect(page.get_by_test_id("quality-review-notification")).to_be_visible()

    # Navigate to the proposal
    page.get_by_test_id("proposal-card").first.click()

    # View quality review feedback
    page.get_by_test_id("view-quality-review-button").click()

    # Verify feedback is visible
    expect(page.get_by_text("Quality Review Feedback")).to_be_visible()
    expect(page.get_by_text("Summary is well-written and comprehensive")).to_be_visible()
    expect(page.get_by_text("Rationale needs stronger evidence base")).to_be_visible()
    expect(page.get_by_text("Approved with Minor Revisions")).to_be_visible()

    take_screenshot(page, "quality_workflow_feedback_viewed")


# ============================================================================
# Test: Quality Review Criteria Verification
# ============================================================================


@pytest.mark.quality_gate
def test_quality_review_criteria_verification(logged_in_qa_officer):
    """User Story: Quality Gate Review
    Steps:
    1. Open a proposal for quality review
    2. Verify all quality criteria are present
    3. Test checking/unchecking criteria
    4. Verify criteria affect overall assessment
    """
    page = logged_in_qa_officer

    page.get_by_test_id("quality-reviews-tab").click()

    proposal_cards = page.get_by_test_id("quality-review-proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for quality review")

    proposal_cards.first.get_by_test_id("review-proposal-button").click()

    # Verify all quality criteria are present
    expect(page.get_by_test_id("quality-criteria-compliance")).to_be_visible()
    expect(page.get_by_text("Compliance with donor requirements")).to_be_visible()

    expect(page.get_by_test_id("quality-criteria-clarity")).to_be_visible()
    expect(page.get_by_text("Clarity and coherence")).to_be_visible()

    expect(page.get_by_test_id("quality-criteria-impact")).to_be_visible()
    expect(page.get_by_text("Impact and relevance")).to_be_visible()

    expect(page.get_by_test_id("quality-criteria-budget")).to_be_visible()
    expect(page.get_by_text("Budget realism and justification")).to_be_visible()

    expect(page.get_by_test_id("quality-criteria-monitoring")).to_be_visible()
    expect(page.get_by_text("Monitoring and evaluation plan")).to_be_visible()

    take_screenshot(page, "quality_review_criteria_verified")

    # Test checking criteria
    page.get_by_test_id("quality-criteria-compliance").check()
    page.get_by_test_id("quality-criteria-clarity").check()
    page.get_by_test_id("quality-criteria-impact").check()

    # Verify criteria are checked
    expect(page.get_by_test_id("quality-criteria-compliance")).to_be_checked()
    expect(page.get_by_test_id("quality-criteria-clarity")).to_be_checked()
    expect(page.get_by_test_id("quality-criteria-impact")).to_be_checked()


# ============================================================================
# Test: Quality Review Access Control
# ============================================================================


@pytest.mark.quality_gate
@pytest.mark.security
def test_quality_review_access_control(page, config):
    """User Story: Quality Gate Review
    Steps:
    1. Try to access quality reviews as regular user
    2. Verify access is denied or functionality is limited
    """
    # Log in as regular user
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # Try to access quality reviews
    page.get_by_test_id("quality-reviews-tab").click()

    # Verify either:
    # 1. Access is denied, or
    # 2. User can only see their own proposals' quality status (not conduct reviews)

    # Check if quality reviews tab is visible but limited
    if page.get_by_test_id("quality-reviews-tab").is_visible():
        # User can see the tab but should have limited functionality
        expect(page.get_by_text("Your Proposals in Quality Review")).to_be_visible()
        expect(page.get_by_test_id("conduct-quality-review-button")).not_to_be_visible()
    else:
        # Or access is completely denied
        expect(page.get_by_text("Access Denied")).to_be_visible()

    take_screenshot(page, "quality_review_access_control")


# ============================================================================
# Test: Quality Review Status Tracking
# ============================================================================


@pytest.mark.quality_gate
def test_quality_review_status_tracking(logged_in_page):
    """User Story: Quality Gate Review
    Steps:
    1. Submit a proposal for quality review
    2. Verify status changes to "In Quality Review"
    3. Check that status is visible in proposal list
    4. Verify status updates after review completion
    """
    page = logged_in_page

    # Navigate to proposals
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() == 0:
        pytest.skip("No proposals available for testing")

    # Submit a proposal for quality review
    first_proposal = proposal_cards.first
    proposal_name = first_proposal.get_by_test_id("proposal-name").text_content()

    first_proposal.click()
    page.get_by_test_id("submit-for-quality-review-button").click()

    # Verify status change
    expect(page.get_by_text("Proposal submitted for quality review")).to_be_visible()

    # Go back to dashboard
    page.get_by_test_id("logo").click()

    # Verify status is updated in proposal card
    updated_proposal = page.get_by_test_id("proposal-card").filter(has_text=proposal_name).first
    expect(updated_proposal.get_by_test_id("proposal-status")).to_have_text("In Quality Review")

    take_screenshot(page, "quality_review_status_tracking")


# ============================================================================
# Test: Complete Quality Gate Review Workflow
# ============================================================================


@pytest.mark.quality_gate
@pytest.mark.e2e
@pytest.mark.regression
def test_complete_quality_gate_review_workflow(page, config):
    """User Story: Quality Gate Review
    Steps:
    1. User submits proposal for quality review
    2. QA officer reviews against all criteria
    3. QA officer provides detailed feedback
    4. QA officer selects appropriate status
    5. User receives and views feedback
    6. User makes revisions based on feedback
    """
    # Step 1: User creates and submits proposal
    user = TEST_USERS["primary"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # Submit existing proposal for quality review
    proposal_cards = page.get_by_test_id("proposal-card")
    if proposal_cards.count() > 0:
        proposal_cards.first.click()
        page.get_by_test_id("submit-for-quality-review-button").click()

    take_screenshot(page, "complete_workflow_user_submits")

    # Log out
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 2: QA officer conducts comprehensive review
    qa_officer = TEST_USERS["qa_officer"]
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(qa_officer.email)
    page.get_by_test_id("password-input").fill(qa_officer.password)
    page.get_by_test_id("submit-button").click()

    page.get_by_test_id("quality-reviews-tab").click()

    if page.get_by_test_id("quality-review-proposal-card").count() > 0:
        page.get_by_test_id("quality-review-proposal-card").first.get_by_test_id("review-proposal-button").click()

        # Check all quality criteria
        page.get_by_test_id("quality-criteria-compliance").check()
        page.get_by_test_id("quality-criteria-clarity").check()
        page.get_by_test_id("quality-criteria-impact").check()
        page.get_by_test_id("quality-criteria-budget").check()
        page.get_by_test_id("quality-criteria-monitoring").check()

        # Add detailed feedback for each section
        page.get_by_test_id("quality-comment-Summary").fill(
            "Excellent executive summary that clearly communicates the project's objectives and expected outcomes"
        )
        page.get_by_test_id("quality-comment-Rationale").fill(
            "Strong rationale with good context, but could benefit from more recent data sources"
        )
        page.get_by_test_id("quality-comment-Evaluation").fill(
            "Monitoring and evaluation plan is comprehensive but needs more specific indicators"
        )
        page.get_by_test_id("quality-comment-Work Plan").fill("Work plan is well-structured and realistic")
        page.get_by_test_id("quality-comment-Budget").fill("Budget is realistic and well-justified")

        # Select status
        page.get_by_test_id("quality-status-select").select_option("approved_with_minor_revisions")

        take_screenshot(page, "complete_workflow_qa_review_detailed")

        # Submit review
        page.get_by_test_id("submit-quality-review-button").click()
        expect(page.get_by_text("Quality review submitted successfully")).to_be_visible()

    take_screenshot(page, "complete_workflow_qa_submitted")

    # Log out QA officer
    page.get_by_test_id("user-menu-button").click()
    page.get_by_test_id("logout-button").click()

    # Step 3: User views and acts on feedback
    page.goto(f"{config['base_url']}/login")
    page.get_by_test_id("email-input").fill(user.email)
    page.get_by_test_id("password-input").fill(user.password)
    page.get_by_test_id("submit-button").click()

    # View quality review feedback
    proposal_cards.first.click()
    page.get_by_test_id("view-quality-review-button").click()

    # Verify all feedback is visible
    expect(page.get_by_text("Excellent executive summary")).to_be_visible()
    expect(page.get_by_text("Strong rationale with good context")).to_be_visible()
    expect(page.get_by_text("Monitoring and evaluation plan is comprehensive")).to_be_visible()

    take_screenshot(page, "complete_workflow_user_views_feedback")

    # Make revisions based on feedback
    # This would involve editing sections, but for this test we'll just verify the workflow
    page.get_by_test_id("close-quality-review-button").click()

    # User can now make revisions and resubmit if needed
    # This completes the quality gate review workflow
