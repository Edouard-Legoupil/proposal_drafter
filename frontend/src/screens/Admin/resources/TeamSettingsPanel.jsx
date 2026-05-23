import React, { useState, useEffect } from 'react';
import { Button, TextField, Select, MenuItem, FormControl, InputLabel, 
         Chip, Box, Typography, CircularProgress, Snackbar, Alert, 
         Card, CardContent, CardHeader, Divider, Grid, Paper } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

export default function TeamSettingsPanel() {
    const [teams, setTeams] = useState([]);
    const [teamSettings, setTeamSettings] = useState([]);
    const [availableSettings, setAvailableSettings] = useState({
        donors: [],
        outcomes: [],
        field_contexts: []
    });
    const [selectedTeam, setSelectedTeam] = useState('');
    const [newSetting, setNewSetting] = useState({
        setting_type: 'donor_focal',
        setting_value: ''
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    
    useEffect(() => {
        fetchInitialData();
    }, []);
    
    const fetchInitialData = async () => {
        setLoading(true);
        try {
            // Fetch teams
            const teamsRes = await fetch(`${API_BASE_URL}/teams`);
            if (teamsRes.ok) {
                const teamsData = await teamsRes.json();
                setTeams(teamsData.teams);
            }
            
            // Fetch available donors, outcomes, field contexts
            const [donorsRes, outcomesRes, fieldContextsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/donors`),
                fetch(`${API_BASE_URL}/outcomes`),
                fetch(`${API_BASE_URL}/field-contexts`)
            ]);
            
            const availableData = {
                donors: [],
                outcomes: [],
                field_contexts: []
            };
            
            if (donorsRes.ok) {
                const d = await donorsRes.json();
                availableData.donors = d.donors || [];
            }
            if (outcomesRes.ok) {
                const o = await outcomesRes.json();
                availableData.outcomes = o.outcomes || [];
            }
            if (fieldContextsRes.ok) {
                const fc = await fieldContextsRes.json();
                availableData.field_contexts = fc.field_contexts || [];
            }
            
            setAvailableSettings(availableData);
            
            // Fetch team settings
            await fetchTeamSettings();
            
        } catch (err) {
            setError('Failed to load data: ' + err.message);
            console.error('Error loading initial data:', err);
        } finally {
            setLoading(false);
        }
    };
    
    const fetchTeamSettings = async () => {
        if (!selectedTeam) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/admin/team-settings?team_id=${selectedTeam}`);
            if (response.ok) {
                const data = await response.json();
                setTeamSettings(data.team_settings || []);
            }
        } catch (err) {
            setError('Failed to load team settings: ' + err.message);
            console.error('Error loading team settings:', err);
        }
    };
    
    const handleTeamChange = (event) => {
        setSelectedTeam(event.target.value);
        setNewSetting({...newSetting, setting_value: ''});
    };
    
    const handleSettingTypeChange = (event) => {
        setNewSetting({...newSetting, setting_type: event.target.value, setting_value: ''});
    };
    
    const handleSettingValueChange = (event) => {
        setNewSetting({...newSetting, setting_value: event.target.value});
    };
    
    const addTeamSetting = async () => {
        if (!selectedTeam || !newSetting.setting_value) {
            setError('Please select a team and setting value');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/admin/team-settings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    team_id: selectedTeam,
                    setting_type: newSetting.setting_type,
                    setting_value: newSetting.setting_value
                }),
                credentials: 'include'
            });
            
            if (response.ok) {
                setSuccess('Team setting added successfully');
                await fetchTeamSettings();
                setNewSetting({...newSetting, setting_value: ''});
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to add team setting');
            }
        } catch (err) {
            setError('Failed to add team setting: ' + err.message);
            console.error('Error adding team setting:', err);
        }
    };
    
    const removeTeamSetting = async (settingId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/team-settings/${settingId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
                setSuccess('Team setting removed successfully');
                await fetchTeamSettings();
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to remove team setting');
            }
        } catch (err) {
            setError('Failed to remove team setting: ' + err.message);
            console.error('Error removing team setting:', err);
        }
    };
    
    const getSettingDisplayName = (type, value) => {
        if (type === 'donor_focal') {
            const donor = availableSettings.donors.find(d => d.id === value);
            return donor ? donor.name : value;
        } else if (type === 'outcome_focal') {
            const outcome = availableSettings.outcomes.find(o => o.id === value);
            return outcome ? outcome.name : value;
        } else if (type === 'field_context_focal') {
            const fieldContext = availableSettings.field_contexts.find(fc => fc.id === value);
            return fieldContext ? fieldContext.name : value;
        }
        return value;
    };
    
    const availableOptions = newSetting.setting_type === 'donor_focal' ? availableSettings.donors :
                          newSetting.setting_type === 'outcome_focal' ? availableSettings.outcomes :
                          availableSettings.field_contexts;
    
    return (
        <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
            <Typography variant="h5" gutterBottom>
                Team Settings Management
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
                Configure settings that will be automatically inherited by all team members.
            </Typography>
            
            {loading ? (
                <Box display="flex" justifyContent="center" my={4}>
                    <CircularProgress />
                </Box>
            ) : (
                <>
                    <Grid container spacing={3}>
                        <Grid item xs={12} md={6}>
                            <Card elevation={2}>
                                <CardHeader title="Add Team Setting" />
                                <CardContent>
                                    <Grid container spacing={2}>
                                        <Grid item xs={12}>
                                            <FormControl fullWidth>
                                                <InputLabel>Team</InputLabel>
                                                <Select
                                                    value={selectedTeam}
                                                    onChange={handleTeamChange}
                                                    label="Team"
                                                >
                                                    {teams.map(team => (
                                                        <MenuItem key={team.id} value={team.id}>
                                                            {team.name}
                                                        </MenuItem>
                                                    ))}
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                        
                                        <Grid item xs={12}>
                                            <FormControl fullWidth>
                                                <InputLabel>Setting Type</InputLabel>
                                                <Select
                                                    value={newSetting.setting_type}
                                                    onChange={handleSettingTypeChange}
                                                    label="Setting Type"
                                                >
                                                    <MenuItem value="donor_focal">Donor Focal</MenuItem>
                                                    <MenuItem value="outcome_focal">Outcome Focal</MenuItem>
                                                    <MenuItem value="field_context_focal">Field Context Focal</MenuItem>
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                        
                                        <Grid item xs={12}>
                                            <FormControl fullWidth>
                                                <InputLabel>Setting Value</InputLabel>
                                                <Select
                                                    value={newSetting.setting_value}
                                                    onChange={handleSettingValueChange}
                                                    label="Setting Value"
                                                    disabled={!selectedTeam}
                                                >
                                                    {availableOptions.map(option => (
                                                        <MenuItem key={option.id} value={option.id}>
                                                            {option.name}
                                                        </MenuItem>
                                                    ))}
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                        
                                        <Grid item xs={12}>
                                            <Button
                                                variant="contained"
                                                color="primary"
                                                startIcon={<AddIcon />}
                                                onClick={addTeamSetting}
                                                disabled={!selectedTeam || !newSetting.setting_value}
                                                fullWidth
                                            >
                                                Add Setting
                                            </Button>
                                        </Grid>
                                    </Grid>
                                </CardContent>
                            </Card>
                        </Grid>
                        
                        <Grid item xs={12} md={6}>
                            <Card elevation={2}>
                                <CardHeader title="Current Team Settings" />
                                <CardContent>
                                    {teamSettings.length === 0 ? (
                                        <Typography color="text.secondary" align="center" py={2}>
                                            No team settings configured
                                        </Typography>
                                    ) : (
                                        <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                                            {teamSettings.map(setting => (
                                                <Card key={setting.id} variant="outlined" sx={{ mb: 2 }}>
                                                    <CardContent>
                                                        <Grid container justifyContent="space-between" alignItems="center">
                                                            <Grid item>
                                                                <Typography variant="subtitle2">
                                                                    {setting.setting_type.replace('_', ' ').toUpperCase()}
                                                                </Typography>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    {getSettingDisplayName(setting.setting_type, setting.setting_value)}
                                                                </Typography>
                                                                <Chip 
                                                                    label={setting.source === 'inherited' ? 'Inherited' : 'Direct'}
                                                                    size="small"
                                                                    color={setting.source === 'inherited' ? 'info' : 'primary'}
                                                                    sx={{ mt: 1 }}
                                                                />
                                                            </Grid>
                                                            <Grid item>
                                                                <Button
                                                                    size="small"
                                                                    color="error"
                                                                    startIcon={<DeleteIcon />}
                                                                    onClick={() => removeTeamSetting(setting.id)}
                                                                >
                                                                    Remove
                                                                </Button>
                                                            </Grid>
                                                        </Grid>
                                                    </CardContent>
                                                </Card>
                                            ))}
                                        </Box>
                                    )}
                                </CardContent>
                            </Card>
                        </Grid>
                    </Grid>
                </>
            )}
            
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
                open={!!success}
                autoHideDuration={3000}
                onClose={() => setSuccess(null)}
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                <Alert severity="success" onClose={() => setSuccess(null)}>
                    {success}
                </Alert>
            </Snackbar>
        </Paper>
    );
}