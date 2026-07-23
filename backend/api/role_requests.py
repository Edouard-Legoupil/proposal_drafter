# Standard Library
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from typing import List

# Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.models.user import User

router = APIRouter()

@router.get("/role-requests")
async def get_available_roles(current_user: dict = Depends(get_current_user)):
    """
    Get all roles that can be requested (excluding system admin)
    """
    try:
        with get_engine().connect() as connection:
            # Get all roles except system admin
            result = connection.execute(
                text("SELECT name FROM roles WHERE name != 'system admin' ORDER BY name")
            )
            roles = [row[0] for row in result.fetchall()]
            
            # Filter out roles the user already has
            user_roles = current_user.get('all_roles', [])
            available_roles = [role for role in roles if role not in user_roles]
            
            return {"available_roles": available_roles}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch available roles: {str(e)}"
        )

@router.post("/role-requests")
async def request_roles(
    request_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a role request
    """
    try:
        requested_roles = request_data.get('requested_roles', [])
        
        if not requested_roles:
            raise HTTPException(
                status_code=400,
                detail="No roles specified for request"
            )
        
        # Validate that user isn't requesting system admin
        if 'system admin' in requested_roles:
            raise HTTPException(
                status_code=403,
                detail="Cannot request system admin role"
            )
        
        # Check if user already has any of the requested roles
        user_roles = current_user.get('all_roles', [])
        already_has = [role for role in requested_roles if role in user_roles]
        
        if already_has:
            raise HTTPException(
                status_code=400,
                detail=f"You already have the following roles: {', '.join(already_has)}"
            )
        
        # Store the role request in the database
        with get_engine().connect() as connection:
            # Check if user already has a pending request for these roles
            existing_request = connection.execute(
                text("""
                SELECT role_id FROM user_role_requests 
                WHERE user_id = :user_id AND role_id IN (
                    SELECT id FROM roles WHERE name = ANY(:role_names)
                )
                """),
                {
                    'user_id': current_user['user_id'],
                    'role_names': requested_roles
                }
            ).fetchall()
            
            if existing_request:
                existing_role_names = [row[0] for row in existing_request]
                raise HTTPException(
                    status_code=400,
                    detail=f"You already have a pending request for: {', '.join(existing_role_names)}"
                )
            
            # Insert the role requests
            for role_name in requested_roles:
                role_result = connection.execute(
                    text("SELECT id FROM roles WHERE name = :name"),
                    {'name': role_name}
                ).fetchone()
                
                if not role_result:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Role '{role_name}' not found"
                    )
                
                role_id = role_result[0]
                
                connection.execute(
                    text("""
                    INSERT INTO user_role_requests (user_id, role_id, requested_at)
                    VALUES (:user_id, :role_id, NOW())
                    """),
                    {'user_id': current_user['user_id'], 'role_id': role_id}
                )
        
        return {
            "message": "Role request submitted successfully",
            "requested_roles": requested_roles
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit role request: {str(e)}"
        )

@router.get("/role-requests/pending")
async def get_pending_requests(current_user: dict = Depends(get_current_user)):
    """
    Get user's pending role requests
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                SELECT r.name as role_name, ur.requested_at
                FROM user_role_requests ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = :user_id
                ORDER BY ur.requested_at DESC
                """),
                {'user_id': current_user['user_id']}
            )
            
            pending_requests = []
            for row in result.fetchall():
                pending_requests.append({
                    'role_name': row[0],
                    'requested_at': row[1].isoformat() if row[1] else None
                })
            
            return {"pending_requests": pending_requests}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch pending requests: {str(e)}"
        )

@router.delete("/role-requests/{role_name}")
async def cancel_role_request(
    role_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a pending role request
    """
    try:
        with get_engine().connect() as connection:
            # Get the role ID
            role_result = connection.execute(
                text("SELECT id FROM roles WHERE name = :name"),
                {'name': role_name}
            ).fetchone()
            
            if not role_result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Role '{role_name}' not found"
                )
            
            role_id = role_result[0]
            
            # Delete the request
            result = connection.execute(
                text("""
                DELETE FROM user_role_requests
                WHERE user_id = :user_id AND role_id = :role_id
                """),
                {'user_id': current_user['user_id'], 'role_id': role_id}
            )
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No pending request found for this role"
                )
        
        return {"message": f"Role request for '{role_name}' cancelled successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel role request: {str(e)}"
        )