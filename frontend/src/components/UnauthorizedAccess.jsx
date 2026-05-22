import React from 'react';
import { Button, Typography, Box, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Lock } from '@mui/icons-material';

const UnauthorizedAccess = ({ component = 'this resource' }) => {
  const navigate = useNavigate();
  
  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '80vh',
      p: 3
    }}>
      <Paper elevation={3} sx={{ p: 4, maxWidth: 600, textAlign: 'center' }}>
        <Lock color="error" sx={{ fontSize: 60, mb: 2 }} />
        <Typography variant="h4" color="error" gutterBottom>
          Access Denied
        </Typography>
        <Typography variant="h6" paragraph>
          You don't have permission to access {component}
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Please contact your administrator to request the appropriate access rights.
        </Typography>
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/dashboard')}
          >
            Return to Dashboard
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/profile')}
          >
            View My Profile
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default UnauthorizedAccess;