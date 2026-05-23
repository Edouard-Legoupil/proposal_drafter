# Standard Library
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

# Internal Modules
from backend.core.db import get_engine
from backend.core.security import is_system_admin

router = APIRouter()

@router.get("/admin/settings-requests")
async def get_all_settings_requests(admin: dict = Depends(is_system_admin)):
    """
    Get all pending settings requests for admin review
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                SELECT 
                    usr.id as request_id,
                    u.id as user_id,
                    u.name as user_name,
                    u.email as user_email,
                    usr.setting_type,
                    usr.setting_value,
                    usr.requested_at
                FROM user_settings_requests usr
                JOIN users u ON usr.user_id = u.id
                WHERE usr.status = 'pending'
                ORDER BY usr.requested_at DESC
                """)
            )
            
            requests = []
            for row in result.fetchall():
                # Get display names for the setting values
                display_name = None
                if row[4] == 'donor_focal':
                    donor = connection.execute(
                        text("SELECT name FROM donors WHERE id = :id"),
                        {'id': row[5]}
                    ).fetchone()
                    display_name = donor[0] if donor else row[5]
                elif row[4] == 'outcome_focal':
                    outcome = connection.execute(
                        text("SELECT name FROM outcomes WHERE id = :id"),
                        {'id': row[5]}
                    ).fetchone()
                    display_name = outcome[0] if outcome else row[5]
                elif row[4] == 'field_context_focal':
                    field_context = connection.execute(
                        text("SELECT name FROM field_contexts WHERE id = :id"),
                        {'id': row[5]}
                    ).fetchone()
                    display_name = field_context[0] if field_context else row[5]
                elif row[4] == 'team_membership':
                    team = connection.execute(
                        text("SELECT name FROM teams WHERE id = :id"),
                        {'id': row[5]}
                    ).fetchone()
                    display_name = team[0] if team else row[5]
                
                requests.append({
                    'request_id': row[0],
                    'user_id': row[1],
                    'user_name': row[2],
                    'user_email': row[3],
                    'setting_type': row[4],
                    'setting_value': row[5],
                    'display_name': display_name,
                    'requested_at': row[6].isoformat() if row[6] else None
                })
            
            return {"settings_requests": requests}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch settings requests: {str(e)}"
        )

@router.post("/admin/settings-requests/{request_id}/approve")
async def approve_settings_request(
    request_id: int,
    admin: dict = Depends(is_system_admin)
):
    """
    Approve a settings request
    """
    try:
        with get_engine().connect() as connection:
            # Get the request details
            request_data = connection.execute(
                text("""
                SELECT user_id, setting_type, setting_value FROM user_settings_requests
                WHERE id = :request_id AND status = 'pending'
                """),
                {'request_id': request_id}
            ).fetchone()
            
            if not request_data:
                raise HTTPException(
                    status_code=404,
                    detail="Request not found or already processed"
                )
            
            user_id = request_data[0]
            setting_type = request_data[1]
            setting_value = request_data[2]
            
            # Check if user already has this setting
            if setting_type == 'donor_focal':
                exists = connection.execute(
                    text("SELECT 1 FROM user_donors WHERE user_id = :user_id AND donor_id = :donor_id"),
                    {'user_id': user_id, 'donor_id': setting_value}
                ).fetchone()
            elif setting_type == 'outcome_focal':
                exists = connection.execute(
                    text("SELECT 1 FROM user_outcomes WHERE user_id = :user_id AND outcome_id = :outcome_id"),
                    {'user_id': user_id, 'outcome_id': setting_value}
                ).fetchone()
            elif setting_type == 'field_context_focal':
                exists = connection.execute(
                    text("SELECT 1 FROM user_field_contexts WHERE user_id = :user_id AND field_context_id = :field_context_id"),
                    {'user_id': user_id, 'field_context_id': setting_value}
                ).fetchone()
            elif setting_type == 'team_membership':
                exists = connection.execute(
                    text("SELECT 1 FROM team_members WHERE user_id = :user_id AND team_id = :team_id"),
                    {'user_id': user_id, 'team_id': setting_value}
                ).fetchone()
            
            if exists:
                # Clean up the request
                connection.execute(
                    text("DELETE FROM user_settings_requests WHERE id = :request_id"),
                    {'request_id': request_id}
                )
                raise HTTPException(
                    status_code=400,
                    detail="User already has this setting"
                )
            
            # Grant the setting to the user
            if setting_type == 'donor_focal':
                connection.execute(
                    text("INSERT INTO user_donors (user_id, donor_id) VALUES (:user_id, :donor_id)"),
                    {'user_id': user_id, 'donor_id': setting_value}
                )
            elif setting_type == 'outcome_focal':
                connection.execute(
                    text("INSERT INTO user_outcomes (user_id, outcome_id) VALUES (:user_id, :outcome_id)"),
                    {'user_id': user_id, 'outcome_id': setting_value}
                )
            elif setting_type == 'field_context_focal':
                connection.execute(
                    text("INSERT INTO user_field_contexts (user_id, field_context_id) VALUES (:user_id, :field_context_id)"),
                    {'user_id': user_id, 'field_context_id': setting_value}
                )
            elif setting_type == 'team_membership':
                connection.execute(
                    text("INSERT INTO team_members (user_id, team_id) VALUES (:user_id, :team_id)"),
                    {'user_id': user_id, 'team_id': setting_value}
                )
            
            # Update the request status
            connection.execute(
                text("""
                UPDATE user_settings_requests
                SET status = 'approved', approved_by = :admin_id, approved_at = NOW()
                WHERE id = :request_id
                """),
                {'request_id': request_id, 'admin_id': admin['user_id']}
            )
        
        return {"message": "Settings request approved successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve settings request: {str(e)}"
        )

@router.post("/admin/settings-requests/{request_id}/reject")
async def reject_settings_request(
    request_data: dict,
    request_id: int,
    admin: dict = Depends(is_system_admin)
):
    """
    Reject a settings request with optional reason
    """
    try:
        rejection_reason = request_data.get('rejection_reason', 'No reason provided')
        
        with get_engine().connect() as connection:
            # Update the request status
            connection.execute(
                text("""
                UPDATE user_settings_requests
                SET status = 'rejected', approved_by = :admin_id, approved_at = NOW(), rejection_reason = :rejection_reason
                WHERE id = :request_id
                """),
                {
                    'request_id': request_id,
                    'admin_id': admin['user_id'],
                    'rejection_reason': rejection_reason
                }
            )
        
        return {"message": "Settings request rejected successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject settings request: {str(e)}"
        )


@router.get("/admin/settings-requests/teams")
async def get_team_settings_requests(admin: dict = Depends(is_system_admin)):
    """
    Get all team settings requests for admin review
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                SELECT 
                    ts.id as setting_id,
                    t.id as team_id,
                    t.name as team_name,
                    ts.setting_type,
                    ts.setting_value,
                    ts.created_at
                FROM team_settings ts
                JOIN teams t ON ts.team_id = t.id
                ORDER BY ts.created_at DESC
                """)
            )
            
            requests = []
            for row in result.fetchall():
                # Get display names for the setting values
                display_name = None
                if row[3] == 'donor_focal':
                    donor = connection.execute(
                        text("SELECT name FROM donors WHERE id = :id"),
                        {'id': row[4]}
                    ).fetchone()
                    display_name = donor[0] if donor else row[4]
                elif row[3] == 'outcome_focal':
                    outcome = connection.execute(
                        text("SELECT name FROM outcomes WHERE id = :id"),
                        {'id': row[4]}
                    ).fetchone()
                    display_name = outcome[0] if outcome else row[4]
                elif row[3] == 'field_context_focal':
                    field_context = connection.execute(
                        text("SELECT name FROM field_contexts WHERE id = :id"),
                        {'id': row[4]}
                    ).fetchone()
                    display_name = field_context[0] if field_context else row[4]
                 
                requests.append({
                    'setting_id': row[0],
                    'team_id': row[1],
                    'team_name': row[2],
                    'setting_type': row[3],
                    'setting_value': row[4],
                    'display_name': display_name,
                    'created_at': row[5].isoformat() if row[5] else None
                })
             
            return {"team_settings": requests}
     
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch team settings: {str(e)}"
        )