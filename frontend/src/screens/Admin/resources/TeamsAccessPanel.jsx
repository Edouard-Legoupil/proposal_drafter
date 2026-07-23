import React, { useState, useEffect } from 'react';
import { useTeamMembership } from '../../../hooks/useTeamMembership';
import { TeamMembershipManagement } from '../../../components/TeamMembershipManagement';
import { useAuth } from '../../../context/AuthContext';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import { Add, Search, Group } from '@mui/icons-material';

/**
 * Teams Access Panel - Admin interface for managing teams and team memberships
 */
export default function TeamsAccessPanel({ resourceId }) {
  const { user } = useAuth();
  const { isLoading, error, requestTeamMembership } = useTeamMembership();
  const [teams, setTeams] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [newTeamName, setNewTeamName] = useState('');
  const [creatingTeam, setCreatingTeam] = useState(false);

  // Fetch teams data
  useEffect(() => {
    const fetchTeams = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || '/api'}/admin/options`, {
          credentials: 'include'
        });

        if (response.ok) {
          const data = await response.json();
          setTeams(data.teams || []);
        }
      } catch (err) {
        console.error('Failed to fetch teams:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  // Filter teams based on search term
  const filteredTeams = teams.filter(team =>
    team.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleTeamSelect = (team) => {
    setSelectedTeam(team);
  };

  const handleBackToList = () => {
    setSelectedTeam(null);
  };

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return;

    setCreatingTeam(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || '/api'}/admin/teams`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newTeamName }),
        credentials: 'include'
      });

      if (response.ok) {
        const result = await response.json();
        setTeams([...teams, result.team]);
        setNewTeamName('');
        // Auto-select the new team
        setSelectedTeam(result.team);
      }
    } catch (err) {
      console.error('Failed to create team:', err);
    } finally {
      setCreatingTeam(false);
    }
  };

  if (!user?.is_admin) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Admin access required to manage teams.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <Group sx={{ verticalAlign: 'middle', mr: 1, fontSize: '1.5rem' }} />
        Team Management
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!selectedTeam ? (
        <>
          {/* Team Search and Create */}
          <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search teams..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ color: 'action.active', mr: 1 }} />
              }}
            />
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setNewTeamName('New Team')}
              disabled={creatingTeam}
            >
              Create Team
            </Button>
          </Box>

          {/* Create Team Form */}
          {newTeamName && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Create New Team
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  <TextField
                    fullWidth
                    variant="outlined"
                    value={newTeamName}
                    onChange={(e) => setNewTeamName(e.target.value)}
                    label="Team Name"
                    disabled={creatingTeam}
                  />
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleCreateTeam}
                    disabled={creatingTeam || !newTeamName.trim()}
                  >
                    {creatingTeam ? 'Creating...' : 'Create'}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => setNewTeamName('')}
                    disabled={creatingTeam}
                  >
                    Cancel
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Teams List */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <CircularProgress />
            </Box>
          ) : filteredTeams.length === 0 ? (
            <Alert severity="info">No teams found</Alert>
          ) : (
            <List>
              {filteredTeams.map((team) => (
                <React.Fragment key={team.id}>
                  <ListItem
                    button
                    onClick={() => handleTeamSelect(team)}
                    sx={{ '&:hover': { backgroundColor: 'action.hover' } }}
                  >
                    <ListItemText
                      primary={team.name}
                      secondary={`ID: ${team.id}`}
                    />
                  </ListItem>
                  <Divider component="li" />
                </React.Fragment>
              ))}
            </List>
          )}
        </>
      ) : (
        <>
          <Button
            variant="outlined"
            startIcon={<ArrowBack />}
            onClick={handleBackToList}
            sx={{ mb: 2 }}
          >
            Back to Teams List
          </Button>

          {/* Team Management Interface */}
          <TeamMembershipManagement team={selectedTeam} />
        </>
      )}
    </Box>
  );
}

// Import ArrowBack icon
import { ArrowBack } from '@mui/icons-material';
