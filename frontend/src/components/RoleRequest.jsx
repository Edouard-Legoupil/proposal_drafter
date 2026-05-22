import React, { useState, useContext } from 'react';
import { Button, Dialog, DialogTitle, DialogContent, DialogActions, 
         FormControl, InputLabel, Select, MenuItem, Chip, Box, 
         Typography, CircularProgress, Snackbar, Alert } from '@mui/material';
import { AuthContext } from './Sidebar/Sidebar';

const RoleRequest = () => {
  const { user } = useContext(AuthContext);
  const [open, setOpen] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  // All roles that can be requested (excluding superadmin)
  const requestableRoles = [
    'proposal writer',
    'knowledge manager donors',
    'knowledge manager outcome',
    'knowledge manager field context',
    'project reviewer',
    'access_metrics',
    'access_template',
    'access_incident',
    'access_quality_gate'
  ];

  const handleOpen = async () => {
    try {
      setLoading(true);
      
      // In a real app, you would fetch available roles from the backend
      // For now, we'll use the requestableRoles list
      const response = await fetch('/api/roles');
      const data = await response.json();
      
      // Filter out roles the user already has and superadmin
      const filteredRoles = requestableRoles.filter(role => 
        !user?.all_roles?.includes(role) && role !== 'system admin'
      );
      
      setAvailableRoles(filteredRoles);
      setOpen(true);
    } catch (err) {
      setError('Failed to load available roles');
      console.error('Error loading roles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedRoles([]);
  };

  const handleRoleChange = (event) => {
    setSelectedRoles(event.target.value);
  };

  const handleSubmit = async () => {
    if (selectedRoles.length === 0) {
      setError('Please select at least one role to request');
      return;
    }

    try {
      setLoading(true);
      
      // Send role request to backend
      const response = await fetch('/api/role-requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id,
          requested_roles: selectedRoles
        })
      });

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => {
          setSuccess(false);
          handleClose();
        }, 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to submit role request');
      }
    } catch (err) {
      setError('Failed to submit role request');
      console.error('Error submitting role request:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Button 
        variant="outlined"
        onClick={handleOpen}
        disabled={loading || !user}
        sx={{ mt: 2 }}
      >
        {loading ? <CircularProgress size={20} /> : 'Request Additional Roles'}
      </Button>

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle>Request Additional Roles</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Select the roles you need to perform your work. Your request will be reviewed by an administrator.
          </Typography>

          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Available Roles</InputLabel>
            <Select
              multiple
              value={selectedRoles}
              onChange={handleRoleChange}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} />
                  ))}
                </Box>
              )}
            >
              {availableRoles.map((role) => (
                <MenuItem key={role} value={role}>
                  {role}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {availableRoles.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              No additional roles available for request.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>Cancel</Button>
          <Button 
            onClick={handleSubmit}
            disabled={loading || selectedRoles.length === 0}
            variant="contained"
            color="primary"
          >
            {loading ? <CircularProgress size={20} /> : 'Submit Request'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={success}
        autoHideDuration={3000}
        onClose={() => setSuccess(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setSuccess(false)}>
          Role request submitted successfully! An administrator will review your request.
        </Alert>
      </Snackbar>
    </div>
  );
};

export default RoleRequest;