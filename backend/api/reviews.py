#  Standard Library
import json
import uuid

#  Third-Party Libraries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

#  Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.core.exceptions import ProposalNotFound, PermissionDenied, ReviewNotFound
from backend.models.schemas import (
    SubmitPeerReviewRequest,
    SubmitReviewRequest,
    AuthorResponseRequest
)
import logging

from backend.repository.review_repository import ReviewRepository
from backend.repository.proposal_repository import ProposalRepository

logger = logging.getLogger(__name__)

router = APIRouter()

review_repository = ReviewRepository()
proposal_repository = ProposalRepository()

@router.post("/proposals/{proposal_id}/review")
async def submit_review(proposal_id: uuid.UUID, request: SubmitReviewRequest, current_user: dict = Depends(get_current_user)):
    """
    Submits a peer review for a proposal, with comments for each section.
    """
    user_id = current_user["user_id"]
    try:
        # Check if the user is assigned to review this proposal.
        if not review_repository.get_reviewer_id(proposal_id, user_id):
            raise PermissionDenied()

        # Get the history ID for the "in_review" status.
        history_id = review_repository.get_in_review_history_id(proposal_id)

        # Delete any existing draft comments.
        review_repository.delete_pending_draft_comments(proposal_id, user_id)

        # Create the new review comments.
        for comment in request.comments:
            if comment.review_text:
                review_repository.create_review_comment(proposal_id, user_id, history_id, comment)

        # If all reviews are completed, update the proposal status.
        if review_repository.get_pending_reviews_count(proposal_id) == 0:
            proposal_repository.update_proposal_status(proposal_id, "pre_submission")

        return {"message": "Review submitted successfully."}
    except Exception as e:
        logger.error(f"[SUBMIT REVIEW ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit review.")

@router.post("/proposals/{proposal_id}/submit-for-review")
async def submit_for_review(proposal_id: uuid.UUID, request: SubmitPeerReviewRequest, current_user: dict = Depends(get_current_user)):
    """
    Submits a proposal for peer review.
    """
    user_id = current_user["user_id"]
    try:
        # Check if the proposal exists and belongs to the user.
        if not proposal_repository.get_proposal_by_id(proposal_id, user_id):
            raise ProposalNotFound(proposal_id)

        # Update the proposal status and create a history entry.
        sections = proposal_repository.get_proposal_generated_sections(proposal_id)
        proposal_repository.update_proposal_status(proposal_id, "in_review")
        proposal_repository.create_proposal_status_history(proposal_id, "in_review", sections)

        # Assign the reviewers.
        for reviewer_info in request.reviewers:
            with get_engine().begin() as connection:
                pending_review = connection.execute(
                    text("""
                        SELECT id FROM proposal_peer_reviews
                        WHERE proposal_id = :proposal_id AND reviewer_id = :reviewer_id AND status = 'pending'
                    """),
                    {"proposal_id": proposal_id, "reviewer_id": reviewer_info.user_id}
                ).fetchone()

                if pending_review:
                    connection.execute(
                        text("""
                            UPDATE proposal_peer_reviews
                            SET deadline = :deadline, updated_at = CURRENT_TIMESTAMP
                            WHERE id = :id
                        """),
                        {"deadline": reviewer_info.deadline, "id": pending_review.id}
                    )
                else:
                    connection.execute(
                        text("""
                            INSERT INTO proposal_peer_reviews (proposal_id, reviewer_id, deadline, status)
                            VALUES (:proposal_id, :reviewer_id, :deadline, 'pending')
                        """),
                        {"proposal_id": proposal_id, "reviewer_id": reviewer_info.user_id, "deadline": reviewer_info.deadline}
                    )

        return {"message": "Proposal submitted for peer review."}
    except Exception as e:
        logger.error(f"[SUBMIT FOR REVIEW ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit for review.")
