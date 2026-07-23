# Standard Library
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

# Internal Modules
from backend.core.db import get_engine
from backend.core.security import is_system_admin

router = APIRouter()

@router.get("/admin/role-requests")
async def get_all_role_requests(admin: dict = Depends(is_system_admin)):
    """
    Get all pending role requests for admin review
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                SELECT 
                    u.id as user_id, 
                    u.name as user_name, 
                    u.email as user_email,
                    r.name as role_name,
                    ur.requested_at
                FROM user_role_requests ur
                JOIN users u ON ur.user_id = u.id
                JOIN roles r ON ur.role_id = r.id
                ORDER BY ur.requested_at DESC
                """)
            )
            
            requests = []
            for row in result.fetchall():
                requests.append({
                    'user_id': row[0],
                    'user_name': row[1],
                    'user_email': row[2],
                    'role_name': row[3],
                    'requested_at': row[4].isoformat() if row[4] else None
                })
            
            return {"role_requests": requests}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch role requests: {str(e)}"
        )

@router.post("/admin/role-requests/{request_id}/approve")
async def approve_role_request(
    request_id: int,
    admin: dict = Depends(is_system_admin)
):
    """
    Approve a role request
    """
    try:
        with get_engine().connect() as connection:
            # Get the request details
            request_data = connection.execute(
                text("""
                SELECT user_id, role_id FROM user_role_requests
                WHERE id = :request_id
                """),
                {'request_id': request_id}
            ).fetchone()
            
            if not request_data:
                raise HTTPException(
                    status_code=404,
                    detail="Role request not found"
                )
            
            user_id = request_data[0]
            role_id = request_data[1]
            
            # Check if user already has this role
            existing_role = connection.execute(
                text("""
                SELECT 1 FROM user_roles
                WHERE user_id = :user_id AND role_id = :role_id
                """),
                {'user_id': user_id, 'role_id': role_id}
            ).fetchone()
            
            if existing_role:
                # Clean up the request
                connection.execute(
                    text("DELETE FROM user_role_requests WHERE id = :request_id"),
                    {'request_id': request_id}
                )
                raise HTTPException(
                    status_code=400,
                    detail="User already has this role"
                )
            
            # Grant the role to the user
            connection.execute(
                text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                """),
                {'user_id': user_id, 'role_id': role_id}
            )
            
            # Remove the request
            connection.execute(
                text("DELETE FROM user_role_requests WHERE id = :request_id"),
                {'request_id': request_id}
            )
        
        return {"message": "Role request approved successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve role request: {str(e)}"
        )

@router.post("/admin/role-requests/{request_id}/reject")
async def reject_role_request(
    request_id: int,
    admin: dict = Depends(is_system_admin)
):
    """
    Reject a role request
    """
    try:
        with get_engine().connect() as connection:
            # Simply remove the request
            result = connection.execute(
                text("DELETE FROM user_role_requests WHERE id = :request_id"),
                {'request_id': request_id}
            )
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Role request not found"
                )
        
        return {"message": "Role request rejected successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject role request: {str(e)}"
        )