# Frontend Role Integration Guide

This document describes how to integrate the new role-based access control system into the frontend components.

## New Roles Added

Four new roles have been added to control access to specific frontend components:

1. **`access_metrics`** - Controls access to `/frontend/src/screens/Dashboard/components/MetricsDashboard/MetricsDashboard.jsx`
2. **`access_template`** - Controls access to:
   - `/frontend/src/screens/DonorTemplateDetail/DonorTemplateDetail.jsx`
   - `/frontend/src/screens/DonorTemplateRequest/DonorTemplateRequest.jsx`
   - `/frontend/src/screens/Dashboard/components/DonorTemplate/DonorTemplate.jsx`
3. **`access_incident`** - Controls access to `/frontend/src/screens/QualityGate/QualityGate.jsx`
4. **`access_quality_gate`** - Controls access to quality gate functionality

## Backend API Changes

### 1. Updated Current User Endpoint

The `/api/users/me` endpoint now returns additional role information:

```json
{
  "user_id": "user-uuid",
  "name": "User Name",
  "email": "user@example.com",
  "roles": ["proposal writer", "knowledge manager donors"],  // Direct roles only
  "all_roles": ["proposal writer", "knowledge manager donors", "access_metrics", "access_template"],  // All roles including inherited
  "is_admin": true,
  "is_sso": false,
  "requested_role_id": null
}
```

### 2. New Role Checking Endpoint

A new endpoint has been added to check if the current user has specific permissions:

```javascript
// GET /api/authorization/check?permission=access_metrics
fetch('/api/authorization/check?permission=access_metrics', {
  credentials: 'include'
})
.then(response => response.json())
.then(data => {
  if (data.has_permission) {
    // User has access
  } else {
    // User does not have access
  }
});
```

### 3. Team Role Management Endpoints (Admin Only)

New admin endpoints for managing team roles:

```javascript
// GET /api/admin/team-roles - Get all team roles
// POST /api/admin/team-roles - Assign role to team
// DELETE /api/admin/team-roles - Remove role from team
```

## Frontend Implementation Guide

### 1. Create a Role Check Utility

Create a utility function in `/frontend/src/utils/roleUtils.js`:

```javascript
/**
 * Check if current user has a specific permission
 * @param {string} permission - Permission to check (e.g., 'access_metrics')
 * @returns {boolean} - True if user has permission
 */
export function hasPermission(permission) {
  // Check if user data is available in Redux/Context
  const user = useSelector(state => state.auth.user);
  
  // Admin users have all permissions
  if (user?.is_admin) return true;
  
  // Check all roles (including inherited)
  return user?.all_roles?.includes(permission) || false;
}

/**
 * Async check for permissions (for server-side validation)
 * @param {string} permission - Permission to check
 * @returns {Promise<boolean>} - Promise resolving to permission status
 */
export async function checkPermission(permission) {
  try {
    const response = await fetch(`/api/authorization/check?permission=${encodeURIComponent(permission)}`, {
      credentials: 'include'
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.has_permission;
    }
    return false;
  } catch (error) {
    console.error('Permission check failed:', error);
    return false;
  }
}
```

### 2. Update Protected Components

#### MetricsDashboard.jsx

```javascript
import { hasPermission } from '../../utils/roleUtils';

function MetricsDashboard() {
  const user = useSelector(state => state.auth.user);
  
  if (!hasPermission('access_metrics')) {
    return <UnauthorizedAccess component="Metrics Dashboard" />;
  }
  
  // ... rest of component
}
```

#### DonorTemplate Components

```javascript
import { hasPermission } from '../../utils/roleUtils';

function DonorTemplateDetail() {
  const user = useSelector(state => state.auth.user);
  
  if (!hasPermission('access_template')) {
    return <UnauthorizedAccess component="Donor Template Detail" />;
  }
  
  // ... rest of component
}
```

#### QualityGate.jsx

```javascript
import { hasPermission } from '../../utils/roleUtils';

function QualityGate() {
  const user = useSelector(state => state.auth.user);
  
  if (!hasPermission('access_incident') && !hasPermission('access_quality_gate')) {
    return <UnauthorizedAccess component="Quality Gate" />;
  }
  
  // ... rest of component
}
```

### 3. Create Unauthorized Access Component

Create `/frontend/src/components/UnauthorizedAccess.jsx`:

```javascript
import React from 'react';
import { Button, Typography, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export function UnauthorizedAccess({ component }) {
  const navigate = useNavigate();
  
  return (
    <Box sx={{ p: 4, textAlign: 'center' }}>
      <Typography variant="h4" color="error" gutterBottom>
        Access Denied
      </Typography>
      <Typography variant="body1" paragraph>
        You do not have permission to access the {component} feature.
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Please contact your administrator to request access.
      </Typography>
      <Button 
        variant="contained"
        onClick={() => navigate('/dashboard')}
        sx={{ mt: 2 }}
      >
        Return to Dashboard
      </Button>
    </Box>
  );
}
```

### 4. Update Navigation Guards

Update your router configuration to include role-based navigation guards:

```javascript
// In your main router configuration
const router = createBrowserRouter([
  {
    path: '/dashboard',
    element: <Dashboard />,
    children: [
      {
        path: 'metrics',
        element: <ProtectedRoute permission="access_metrics"><MetricsDashboard /></ProtectedRoute>
      },
      {
        path: 'templates',
        element: <ProtectedRoute permission="access_template"><DonorTemplates /></ProtectedRoute>
      },
      {
        path: 'quality-gate',
        element: <ProtectedRoute permission="access_quality_gate"><QualityGate /></ProtectedRoute>
      }
    ]
  }
]);

// Create ProtectedRoute component
function ProtectedRoute({ permission, children }) {
  const user = useSelector(state => state.auth.user);
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (!hasPermission(permission)) {
    return <UnauthorizedAccess component={children.type.name} />;
  }
  
  return children;
}
```

### 5. Update Admin Interface

Add team role management to the admin interface:

```javascript
// AdminTeamRoles.jsx
import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { 
  Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Paper, Button, 
  Select, MenuItem, FormControl, InputLabel
} from '@mui/material';

export function AdminTeamRoles() {
  const [teams, setTeams] = useState([]);
  const [roles, setRoles] = useState([]);
  const [teamRoles, setTeamRoles] = useState({});
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const user = useSelector(state => state.auth.user);
  
  useEffect(() => {
    async function fetchData() {
      // Fetch teams
      const teamsResponse = await fetch('/api/teams');
      const teamsData = await teamsResponse.json();
      setTeams(teamsData.teams);
      
      // Fetch roles
      const rolesResponse = await fetch('/api/roles');
      const rolesData = await rolesResponse.json();
      setRoles(rolesData);
      
      // Fetch current team roles
      const teamRolesResponse = await fetch('/api/admin/team-roles');
      const teamRolesData = await teamRolesResponse.json();
      
      // Organize by team
      const organized = {};
      teamRolesData.forEach(tr => {
        if (!organized[tr.team_id]) {
          organized[tr.team_id] = [];
        }
        organized[tr.team_id].push(tr.role_id);
      });
      setTeamRoles(organized);
    }
    
    if (user?.is_admin) {
      fetchData();
    }
  }, [user]);
  
  const assignRoleToTeam = async () => {
    if (!selectedTeam || !selectedRole) return;
    
    try {
      const response = await fetch('/api/admin/team-roles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team_id: selectedTeam,
          role_id: selectedRole
        }),
        credentials: 'include'
      });
      
      if (response.ok) {
        // Refresh data
        window.location.reload();
      }
    } catch (error) {
      console.error('Failed to assign role:', error);
    }
  };
  
  const removeRoleFromTeam = async (teamId, roleId) => {
    try {
      const response = await fetch(`/api/admin/team-roles`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team_id: teamId,
          role_id: roleId
        }),
        credentials: 'include'
      });
      
      if (response.ok) {
        // Refresh data
        window.location.reload();
      }
    } catch (error) {
      console.error('Failed to remove role:', error);
    }
  };
  
  if (!user?.is_admin) {
    return <UnauthorizedAccess component="Team Role Management" />;
  }
  
  return (
    <div>
      <h2>Team Role Management</h2>
      
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', alignItems: 'center' }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Team</InputLabel>
          <Select
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
            label="Team"
          >
            {teams.map(team => (
              <MenuItem key={team.id} value={team.id}>{team.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Role</InputLabel>
          <Select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            label="Role"
          >
            {roles.map(role => (
              <MenuItem key={role.id} value={role.id}>{role.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        
        <Button 
          variant="contained"
          color="primary"
          onClick={assignRoleToTeam}
          disabled={!selectedTeam || !selectedRole}
        >
          Assign Role to Team
        </Button>
      </div>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Team</TableCell>
              <TableCell>Assigned Roles</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {teams.map(team => (
              <TableRow key={team.id}>
                <TableCell>{team.name}</TableCell>
                <TableCell>
                  {teamRoles[team.id]?.map(roleId => {
                    const role = roles.find(r => r.id === roleId);
                    return role ? role.name : 'Unknown Role';
                  }).join(', ') || 'No roles assigned'}
                </TableCell>
                <TableCell>
                  {teamRoles[team.id]?.map(roleId => (
                    <Button 
                      key={roleId}
                      variant="outlined"
                      color="error"
                      size="small"
                      onClick={() => removeRoleFromTeam(team.id, roleId)}
                      style={{ marginRight: '5px', marginBottom: '5px' }}
                    >
                      Remove
                    </Button>
                  ))}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
```

## Backend API Implementation (To Be Added)

The following endpoints need to be implemented in the backend:

### 1. Authorization Check Endpoint

```python
# In backend/api/authorization.py

@router.get("/check")
async def check_permission(
    permission: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check if current user has a specific permission.
    """
    has_access = has_permission(current_user, permission)
    return {"has_permission": has_access, "permission": permission}
```

### 2. Team Role Management Endpoints

```python
# In backend/api/admin.py

@router.get("/team-roles")
async def get_team_roles(admin: dict = Depends(is_system_admin)):
    """
    Get all team role assignments.
    """
    try:
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                SELECT tr.team_id, t.name as team_name, tr.role_id, r.name as role_name
                FROM team_roles tr
                JOIN teams t ON tr.team_id = t.id
                JOIN roles r ON tr.role_id = r.id
                ORDER BY t.name, r.name
                """)
            )
            team_roles = [dict(row) for row in result.mappings()]
            return team_roles
    except Exception as e:
        logger.error(f"[GET TEAM ROLES ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve team roles.")

@router.post("/team-roles")
async def assign_role_to_team(
    request: Request,
    admin: dict = Depends(is_system_admin)
):
    """
    Assign a role to a team.
    """
    try:
        data = await request.json()
        team_id = data.get("team_id")
        role_id = data.get("role_id")
        
        if not team_id or not role_id:
            raise HTTPException(status_code=400, detail="team_id and role_id are required")
        
        # Verify team and role exist
        with get_engine().connect() as connection:
            # Check team exists
            team_result = connection.execute(
                text("SELECT 1 FROM teams WHERE id = :team_id"),
                {"team_id": team_id}
            ).fetchone()
            
            if not team_result:
                raise HTTPException(status_code=404, detail="Team not found")
            
            # Check role exists
            role_result = connection.execute(
                text("SELECT 1 FROM roles WHERE id = :role_id"),
                {"role_id": role_id}
            ).fetchone()
            
            if not role_result:
                raise HTTPException(status_code=404, detail="Role not found")
            
            # Check if assignment already exists
            exists_result = connection.execute(
                text("SELECT 1 FROM team_roles WHERE team_id = :team_id AND role_id = :role_id"),
                {"team_id": team_id, "role_id": role_id}
            ).fetchone()
            
            if exists_result:
                return {"message": "Role already assigned to team"}
            
            # Assign role to team
            connection.execute(
                text("INSERT INTO team_roles (team_id, role_id) VALUES (:team_id, :role_id)"),
                {"team_id": team_id, "role_id": role_id}
            )
            
            return {"message": "Role assigned to team successfully"}
    
    except Exception as e:
        logger.error(f"[ASSIGN ROLE TO TEAM ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not assign role to team.")

@router.delete("/team-roles")
async def remove_role_from_team(
    request: Request,
    admin: dict = Depends(is_system_admin)
):
    """
    Remove a role from a team.
    """
    try:
        data = await request.json()
        team_id = data.get("team_id")
        role_id = data.get("role_id")
        
        if not team_id or not role_id:
            raise HTTPException(status_code=400, detail="team_id and role_id are required")
        
        with get_engine().connect() as connection:
            # Remove role from team
            result = connection.execute(
                text("DELETE FROM team_roles WHERE team_id = :team_id AND role_id = :role_id"),
                {"team_id": team_id, "role_id": role_id}
            )
            
            if result.rowcount === 0:
                raise HTTPException(status_code=404, detail="Team role assignment not found")
            
            return {"message": "Role removed from team successfully"}
    
    except Exception as e:
        logger.error(f"[REMOVE ROLE FROM TEAM ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not remove role from team.")
```

## Testing the Implementation

Run the new tests to verify the backend functionality:

```bash
pytest backend/tests/test_team_roles.py -v
```

## Migration Steps

1. **Apply database migration**: Run the team roles migration SQL
2. **Update seed data**: Ensure new roles are included in seed data
3. **Deploy backend changes**: Update authorization logic and API endpoints
4. **Update frontend**: Implement role checks in protected components
5. **Test thoroughly**: Verify both direct and inherited role access

## Security Considerations

- **Admin Bypass**: System admins automatically have all permissions
- **Role Inheritance**: Users inherit roles from their teams
- **Permission Checking**: Always check `all_roles` for comprehensive access control
- **API Security**: All endpoints require authentication and proper authorization

This implementation provides a flexible, team-based role inheritance system that allows for granular access control while maintaining security and ease of administration.