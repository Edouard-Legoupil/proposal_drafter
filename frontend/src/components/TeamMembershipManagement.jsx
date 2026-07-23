import React, { useState, useEffect } from 'react';
import { useTeamMembership } from '../hooks/useTeamMembership';
import { useAuth } from '../context/AuthContext';
import {
  Box,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip
} from '@mui/material';
import { Check, Close, Add, Group, PersonAdd } from '@mui/icons-material';

/**
 * Team Membership Management Component
 * Allows team leaders and admins to manage team memberships and roles
 */
export function TeamMembershipManagement({ team }) {
  const { user } = useAuth();
  const {
    isLoading,
    error,
    getPendingRequests,
    approveMembership,
    rejectMembership,
    getTeamRoles,
    assignRoleToTeam,
    removeRoleFromTeam,
    canApproveMembership,
    canManageTeamRoles
  } = useTeamMembership();

  const [pendingRequests, setPendingRequests] = useState([]);
  const [teamRoles, setTeamRoles] = useState([]);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState('');
  const [showRoleDialog, setShowRoleDialog] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Refresh data
  const refreshData = async () => {
    setRefreshing(true);
    try {
      if (canApproveMembership(team.id)) {
        const requests = await getPendingRequests(team.id);
        setPendingRequests(requests);
      }

      if (canManageTeamRoles(team.id)) {
        const roles = await getTeamRoles(team.id);
        setTeamRoles(roles);
      }
    } catch (err) {
      console.error('Failed to refresh team data:', err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    refreshData();

    // Load available roles (this would come from a roles API in a real app)
    setAvailableRoles([
      { id: 1, name: 'access_metrics' },
      { id: 2, name: 'access_template' },
      { id: 3, name: 'access_incident' },
      { id: 4, name: 'access_quality_gate' },
      { id: 998, name: 'TEAM_LEADER' }
    ]);
  }, [team.id, canApproveMembership, canManageTeamRoles]);

  const handleApprove = async (userId) => {
    try {
      const success = await approveMembership(team.id, userId);
      if (success) {
        await refreshData();
      }
    } catch (err) {
      console.error('Failed to approve membership:', err);
    }
  };

  const handleReject = async (userId) => {
    try {
      const success = await rejectMembership(team.id, userId);
      if (success) {
        await refreshData();
      }
    } catch (err) {
      console.error('Failed to reject membership:', err);
    }
  };

  const handleAssignRole = async () => {
    if (!selectedRole) return;

    try {
      const success = await assignRoleToTeam(team.id, selectedRole);
      if (success) {
        setShowRoleDialog(false);
        setSelectedRole('');
        await refreshData();
      }
    } catch (err) {
      console.error('Failed to assign role:', err);
    }
  };

  const handleRemoveRole = async (roleId) => {
    try {
      const success = await removeRoleFromTeam(team.id, roleId);
      if (success) {
        await refreshData();
      }
    } catch (err) {
      console.error('Failed to remove role:', err);
    }
  };

  if (!team) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="info">No team selected</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        <Group sx={{ verticalAlign: 'middle', mr: 1 }} />
        {team.name} Management
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Team Information */}
      <Box sx={{ mb: 3, p: 2, backgroundColor: 'background.paper', borderRadius: 1 }}>
        <Typography variant="subtitle1" gutterBottom>
          Team Information
        </Typography>
        <Typography><strong>ID:</strong> {team.id}</Typography>
        <Typography><strong>Name:</strong> {team.name}</Typography>
        <Typography><strong>Description:</strong> {team.description || 'No description'}</Typography>
      </Box>

      {/* Pending Membership Requests */}
      {canApproveMembership(team.id) && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            <PersonAdd sx={{ verticalAlign: 'middle', mr: 1 }} />
            Pending Membership Requests
          </Typography>

          {refreshing ? (
            <CircularProgress />
          ) : pendingRequests.length === 0 ? (
            <Alert severity="info">No pending membership requests</Alert>
          ) : (
            <List>
              {pendingRequests.map((request) => (
                <ListItem key={request.user_id} secondaryAction={
                  <>
                    <IconButton
                      edge="end"
                      aria-label="approve"
                      onClick={() => handleApprove(request.user_id)}
                      color="success"
                      disabled={isLoading}
                    >
                      <Check />
                    </IconButton>
                    <IconButton
                      edge="end"
                      aria-label="reject"
                      onClick={() => handleReject(request.user_id)}
                      color="error"
                      disabled={isLoading}
                      sx={{ ml: 1 }}
                    >
                      <Close />
                    </IconButton>
                  </>
                }>
                  <ListItemText
                    primary={request.user_name}
                    secondary={request.user_email}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      )}

      {/* Team Roles Management */}
      {canManageTeamRoles(team.id) && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Team Roles
          </Typography>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setShowRoleDialog(true)}
              disabled={isLoading}
            >
              Assign Role
            </Button>
          </Box>

          {teamRoles.length === 0 ? (
            <Alert severity="info">No roles assigned to this team</Alert>
          ) : (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {teamRoles.map((role) => (
                <Chip
                  key={role.role_id}
                  label={role.role_name}
                  onDelete={() => handleRemoveRole(role.role_id)}
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* Role Assignment Dialog */}
      <Dialog open={showRoleDialog} onClose={() => setShowRoleDialog(false)}>
        <DialogTitle>Assign Role to Team</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2, minWidth: 200 }}>
            <InputLabel id="role-select-label">Role</InputLabel>
            <Select
              labelId="role-select-label"
              id="role-select"
              value={selectedRole}
              label="Role"
              onChange={(e) => setSelectedRole(e.target.value)}
            >
              {availableRoles.map((role) => (
                <MenuItem key={role.id} value={role.id}>{role.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowRoleDialog(false)}>Cancel</Button>
          <Button
            onClick={handleAssignRole}
            variant="contained"
            color="primary"
            disabled={!selectedRole || isLoading}
          >
            Assign
          </Button>
        </DialogActions>
      </Dialog>

      {/* Loading indicator */}
      {(isLoading || refreshing) && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <CircularProgress />
        </Box>
      )}
    </Box>
  );
}
