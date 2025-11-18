from fastapi import HTTPException

class ProposalNotFound(HTTPException):
    def __init__(self, proposal_id: str):
        super().__init__(status_code=404, detail=f"Proposal with id {proposal_id} not found.")

class PermissionDenied(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail="You do not have permission to perform this action.")

class InvalidStatus(HTTPException):
    def __init__(self, status: str):
        super().__init__(status_code=400, detail=f"Invalid status: {status}")

class ReviewNotFound(HTTPException):
    def __init__(self, review_id: str):
        super().__init__(status_code=404, detail=f"Review with id {review_id} not found.")
