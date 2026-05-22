# Standard Library
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from typing import List, Dict, Any

# Internal Modules
from backend.core.db import get_engine
from backend.core.security import get_current_user

router = APIRouter()

@router.get("/settings/requests")
async def get_available_settings(current_user: dict = Depends(get_current_user)):
    """
    Get available settings that can be requested
    """
    try:
        with get_engine().connect() as connection:
            # Get donors user doesn't already have
            donor_result = connection.execute(
                text("""
                SELECT d.id, d.name
                FROM donors d
                WHERE d.id NOT IN (
                    SELECT setting_value FROM user_settings_requests 
                    WHERE user_id = :user_id AND setting_type = 'donor_focal' AND status = 'approved'
                    UNION
                    SELECT donor_id FROM user_donors WHERE user_id = :user_id
                )
                ORDER BY d.name
                """),
                {'user_id': current_user['user_id']}
            ).fetchall()
            
            # Get outcomes user doesn't already have
            outcome_result = connection.execute(
                text("""
                SELECT o.id, o.name
                FROM outcomes o
                WHERE o.id NOT IN (
                    SELECT setting_value FROM user_settings_requests 
                    WHERE user_id = :user_id AND setting_type = 'outcome_focal' AND status = 'approved'
                    UNION
                    SELECT outcome_id FROM user_outcomes WHERE user_id = :user_id
                )
                ORDER BY o.name
                """),
                {'user_id': current_user['user_id']}
            ).fetchall()
            
            # Get field contexts user doesn't already have
            field_context_result = connection.execute(
                text("""
                SELECT fc.id, fc.name
                FROM field_contexts fc
                WHERE fc.id NOT IN (
                    SELECT setting_value FROM user_settings_requests 
                    WHERE user_id = :user_id AND setting_type = 'field_context_focal' AND status = 'approved'
                    UNION
                    SELECT field_context_id FROM user_field_contexts WHERE user_id = :user_id
                )
                ORDER BY fc.name
                """),
                {'user_id': current_user['user_id']}
            ).fetchall()
            
            # Get teams user doesn't already belong to
            team_result = connection.execute(
                text("""
                SELECT t.id, t.name
                FROM teams t
                WHERE t.id NOT IN (
                    SELECT setting_value FROM user_settings_requests 
                    WHERE user_id = :user_id AND setting_type = 'team_membership' AND status = 'approved'
                    UNION
                    SELECT team_id FROM team_members WHERE user_id = :user_id
                )
                ORDER BY t.name
                """),
                {'user_id': current_user['user_id']}
            ).fetchall()
            
            return {
                "available_settings": {
                    "donor_focal": [{"id": row[0], "name": row[1]} for row in donor_result],
                    "outcome_focal": [{"id": row[0], "name": row[1]} for row in outcome_result],
                    "field_context_focal": [{"id": row[0], "name": row[1]} for row in field_context_result],
                    "team_membership": [{"id": row[0], "name": row[1]} for row in team_result]
                }
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch available settings: {str(e)}"
        )

@router.post("/settings/requests")
async def request_setting(
    request_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a setting request
    """
    try:
        setting_type = request_data.get('setting_type')
        setting_value = request_data.get('setting_value')
        
        # Validate input
        if not setting_type or not setting_value:
            raise HTTPException(
                status_code=400,
                detail="setting_type and setting_value are required"
            )
        
        # Validate setting type
        valid_types = ['donor_focal', 'outcome_focal', 'field_context_focal', 'team_membership']
        if setting_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid setting type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Check if user already has this setting
        with get_engine().connect() as connection:
            # Check if already has the setting
            if setting_type == 'donor_focal':
                exists = connection.execute(
                    text("SELECT 1 FROM user_donors WHERE user_id = :user_id AND donor_id = :donor_id"),
                    {'user_id': current_user['user_id'], 'donor_id': setting_value}
                ).fetchone()
            elif setting_type == 'outcome_focal':
                exists = connection.execute(
                    text("SELECT 1 FROM user_outcomes WHERE user_id = :user_id AND outcome_id = :outcome_id"),
                    {'user_id': current_user['user_id'], 'outcome_id': setting_value}
                ).fetchone()
            elif setting_type == 'field_context_focal':
                exists = connection.execute(
                    text("SELECT 1 FROM user_field_contexts WHERE user_id = :user_id AND field_context_id = :field_context_id"),
                    {'user_id': current_user['user_id'], 'field_context_id': setting_value}
                ).fetchone()
            elif setting_type == 'team_membership':
                exists = connection.execute(
                    text("SELECT 1 FROM team_members WHERE user_id = :user_id AND team_id = :team_id"),
                    {'user_id': current_user['user_id'], 'team_id': setting_value}
                ).fetchone()
            
            if exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"You already have this {setting_type.replace('_', ' ')}"
                )
            
            # Check if already has a pending request
            pending = connection.execute(
                text("""
                SELECT 1 FROM user_settings_requests 
                WHERE user_id = :user_id AND setting_type = :setting_type 
                AND setting_value = :setting_value AND status = 'pending'
                """),
                {
                    'user_id': current_user['user_id'],
                    'setting_type': setting_type,
                    'setting_value': setting_value
                }
            ).fetchone()
            
            if pending:
                raise HTTPException(
                    status_code=400,
                    detail="You already have a pending request for this setting"
                )
            
            # Insert the request
            connection.execute(
                text("""
                INSERT INTO user_settings_requests 
                (user_id, setting_type, setting_value, status)
                VALUES (:user_id, :setting_type, :setting_value, 'pending')
                """),
                {
                    'user_id': current_user['user_id'],
                    'setting_type': setting_type,
                    'setting_value': setting_value
                }
            )
        
        return {
            "message": "Setting request submitted successfully",
            "setting_type": setting_type,
            "setting_value": setting_value
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit setting request: {str(e)}"
        )

@router.get("/settings/requests/pending")
async def get_pending_settings_requests(current_user: dict = Depends(get_current_user)):
    """
    Get user's pending settings requests
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                SELECT id, setting_type, setting_value, requested_at
                FROM user_settings_requests
                WHERE user_id = :user_id AND status = 'pending'
                ORDER BY requested_at DESC
                """),
                {'user_id': current_user['user_id']}
            )
            
            requests = []
            for row in result.fetchall():
                # Get display names for the setting values
                display_name = None
                if row[1] == 'donor_focal':
                    donor = connection.execute(
                        text("SELECT name FROM donors WHERE id = :id"),
                        {'id': row[2]}
                    ).fetchone()
                    display_name = donor[0] if donor else row[2]
                elif row[1] == 'outcome_focal':
                    outcome = connection.execute(
                        text("SELECT name FROM outcomes WHERE id = :id"),
                        {'id': row[2]}
                    ).fetchone()
                    display_name = outcome[0] if outcome else row[2]
                elif row[1] == 'field_context_focal':
                    field_context = connection.execute(
                        text("SELECT name FROM field_contexts WHERE id = :id"),
                        {'id': row[2]}
                    ).fetchone()
                    display_name = field_context[0] if field_context else row[2]
                elif row[1] == 'team_membership':
                    team = connection.execute(
                        text("SELECT name FROM teams WHERE id = :id"),
                        {'id': row[2]}
                    ).fetchone()
                    display_name = team[0] if team else row[2]
                
                requests.append({
                    'request_id': row[0],
                    'setting_type': row[1],
                    'setting_value': row[2],
                    'display_name': display_name,
                    'requested_at': row[3].isoformat() if row[3] else None
                })
            
            return {"pending_requests": requests}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch pending settings requests: {str(e)}"
        )

@router.delete("/settings/requests/{request_id}")
async def cancel_setting_request(
    request_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a pending setting request
    """
    try:
        with get_engine().connect() as connection:
            # Verify the request belongs to the user
            request_data = connection.execute(
                text("""
                SELECT user_id FROM user_settings_requests
                WHERE id = :request_id AND status = 'pending'
                """),
                {'request_id': request_id}
            ).fetchone()
            
            if not request_data:
                raise HTTPException(
                    status_code=404,
                    detail="Request not found or already processed"
                )
            
            if request_data[0] != current_user['user_id']:
                raise HTTPException(
                    status_code=403,
                    detail="You can only cancel your own requests"
                )
            
            # Delete the request
            connection.execute(
                text("DELETE FROM user_settings_requests WHERE id = :request_id"),
                {'request_id': request_id}
            )
        
        return {"message": "Setting request cancelled successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel setting request: {str(e)}"
        )