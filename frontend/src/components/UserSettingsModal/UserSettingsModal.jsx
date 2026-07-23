import { useState, useEffect } from 'react';
import Select from 'react-select';
import './UserSettingsModal.css';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

export default function UserSettingsModal({ show, onClose }) {
    const [options, setOptions] = useState({
        teams: []
    });
    const [selectedTeams, setSelectedTeams] = useState([]);
    const [pendingRequests, setPendingRequests] = useState({
        teams: []
    });
    const [inheritedSettings, setInheritedSettings] = useState({
        teams: []
    });
    const [teamMemberships, setTeamMemberships] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (show) {
            fetchInitialData();
        }
    }, [show]);

    const fetchInitialData = async () => {
        setLoading(true);
        try {
            const [settingsRes, teamsRes, pendingRes, inheritedRes] = await Promise.all([
                fetch(`${API_BASE_URL}/users/me/settings`, { credentials: 'include' }),
                fetch(`${API_BASE_URL}/teams`),
                fetch(`${API_BASE_URL}/settings/requests/pending`, { credentials: 'include' }),
                fetch(`${API_BASE_URL}/users/me/approved-settings`, { credentials: 'include' })
            ]);

            let teamsData = [];


            if (teamsRes.ok) {
                const t = await teamsRes.json();
                teamsData = t.teams || [];
            }

            const teamOptions = teamsData.map(t => ({ value: t.id, label: t.name }));

            setOptions({
                teams: teamOptions
            });

            // Process pending requests
            if (pendingRes.ok) {
                const pendingData = await pendingRes.json();
                const pendingMap = {
                    roles: [],
                    donors: [],
                    outcomes: [],
                    field_contexts: [],
                    teams: []
                };

                pendingData.pending_requests.forEach(request => {
                    if (request.setting_type === 'team_membership') pendingMap.teams.push(request.setting_value);
                });

                setPendingRequests(pendingMap);
            }

            // Process inherited settings
            if (inheritedRes.ok) {
                const inheritedData = await inheritedRes.json();
                const inheritedMap = {
                    roles: [],
                    donors: [],
                    outcomes: [],
                    field_contexts: [],
                    teams: []
                };

                inheritedData.approved_settings.forEach(setting => {
                    if (setting.source === 'inherited') {
                        if (setting.setting_type === 'team_membership') inheritedMap.teams.push(setting.setting_value);
                    }
                });

                setInheritedSettings(inheritedMap);
            }

            if (settingsRes.ok) {
                const data = await settingsRes.json();
                if (data) {

                    setTeamMemberships(data.team_memberships || []);


                    // Set selected teams, but ensure inherited teams are always included and can't be removed
                    const directTeams = teamOptions.filter(t => allTeamIds.includes(t.value));
                    const inheritedTeams = teamOptions.filter(t => inheritedSettings.teams.includes(t.value));
                    const allSelectedTeams = [...directTeams, ...inheritedTeams.filter(
                        inheritedTeam => !directTeams.some(directTeam => directTeam.value === inheritedTeam.value)
                    )];
                    setSelectedTeams(allSelectedTeams);
                }
            }
        } catch (error) {
            console.error("Failed to fetch initial data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // When saving, we keep existing team_memberships as is, and anything new goes to requested_team_memberships
        // Actually, the backend update_user_settings currently deletes and re-inserts based on what's sent.
        // So we send the current granted team_memberships and the current requested team_memberships (anything selected that is NOT granted).



        // For team memberships, we need to separate existing teams from new team requests
        const currentTeamIds = selectedTeams.map(t => t.value);
        const existingTeamIds = teamMemberships || []; // Teams the user already belongs to
        const inheritedTeamIds = inheritedSettings.teams || []; // Teams inherited from team memberships

        // Teams that are already approved (should be sent to update actual memberships)
        // But exclude inherited teams since they can't be removed directly
        const approvedTeams = currentTeamIds.filter(teamId =>
            existingTeamIds.includes(teamId) && !inheritedTeamIds.includes(teamId)
        );

        // Teams that are new requests (should go through approval process)
        const newTeamRequests = currentTeamIds.filter(teamId =>
            !existingTeamIds.includes(teamId) && !inheritedTeamIds.includes(teamId)
        );



        const settings = {
            team_memberships: approvedTeams, // Only send already approved teams to direct update
            requested_team_memberships: newRequestedTeams
        };

        try {
            // First update the direct settings (roles, approved teams, etc.)
            const response = await fetch(`${API_BASE_URL}/users/me/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
                credentials: 'include'
            });

            if (!response.ok) {
                console.error("Failed to update settings");
                alert("Failed to update settings.");
                return;
            }

            // The backend now handles requested settings automatically
            if (newTeamRequests.length > 0 || newRequestedDonors.length > 0 || newRequestedOutcomes.length > 0 || newRequestedFieldContexts.length > 0) {
                alert(`Successfully submitted your access requests. New items will appear in orange until approved by an administrator.`);
            }

            onClose();
        } catch (error) {
            console.error("Failed to update settings:", error);
            alert("An error occurred while updating settings.");
        }
    };

    const roleStyles = {
        multiValue: (styles, { data }) => {
            const isRequested = !grantedRoles.includes(data.value);
            return {
                ...styles,
                backgroundColor: isRequested ? '#ff9800' : styles.backgroundColor,
                color: isRequested ? 'white' : styles.color,
            };
        },
        multiValueLabel: (styles, { data }) => {
            const isRequested = !grantedRoles.includes(data.value);
            return {
                ...styles,
                color: isRequested ? 'white' : styles.color,
            };
        },
        multiValueRemove: (styles, { data }) => {
            const isRequested = !grantedRoles.includes(data.value);
            return {
                ...styles,
                color: isRequested ? 'white' : styles.color,
                ':hover': {
                    backgroundColor: isRequested ? '#e68a00' : styles[':hover']?.backgroundColor,
                    color: isRequested ? 'white' : styles[':hover']?.color,
                },
            };
        },
    };

    const pendingStyles = (settingType) => ({
        multiValue: (styles, { data }) => {
            const isPending = pendingRequests[settingType]?.includes(data.value);
            const isInherited = inheritedSettings[settingType]?.includes(data.value);

            return {
                ...styles,
                backgroundColor: isPending ? '#ff9800' : isInherited ? '#4caf50' : styles.backgroundColor,
                color: (isPending || isInherited) ? 'white' : styles.color,
            };
        },
        multiValueLabel: (styles, { data }) => {
            const isPending = pendingRequests[settingType]?.includes(data.value);
            const isInherited = inheritedSettings[settingType]?.includes(data.value);

            return {
                ...styles,
                color: (isPending || isInherited) ? 'white' : styles.color,
            };
        },
        multiValueRemove: (styles, { data }) => {
            const isPending = pendingRequests[settingType]?.includes(data.value);
            const isInherited = inheritedSettings[settingType]?.includes(data.value);

            return {
                ...styles,
                color: (isPending || isInherited) ? 'white' : styles.color,
                ':hover': {
                    backgroundColor: isPending ? '#e68a00' : isInherited ? '#45a049' : styles[':hover']?.backgroundColor,
                    color: (isPending || isInherited) ? 'white' : styles[':hover']?.color,
                },
                display: isInherited ? 'none' : styles.display  // Hide remove button for inherited settings
            };
        },
    });

    if (!show) return null;

    return (
        <div className="user-settings-overlay" onClick={onClose}>
            <div className="user-settings-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Access and Permissions Management</h2>
                    <button className="close-x" onClick={onClose}>&times;</button>
                </div>

                {loading ? (
                    <div className="modal-loading">Loading settings...</div>
                ) : (
                    <form onSubmit={handleSubmit} className="modal-form">
                        <div className="modal-instructions">
                            <h3>Access and Permissions Management</h3>
                            <p>This form allows you to request membership to specific teams where access levels are defined. You can join multiple teams, and will inherit access rights and focal areas from each team. This includes:</p>
                            <ul className="instruction-list">
                                <li><strong>Roles:</strong> Determine what actions you can perform in the system. Requested roles appear in orange until approved.</li>
                                <li><strong>Donor Focal:</strong> Donors that will be included by default in the proposals and knowledge cards you create.</li>
                                <li><strong>Outcomes Focal:</strong> Outcomes that will be included by default in the proposals you create.</li>
                                <li><strong>Field Contexts Focal:</strong> Countries/regions that will be included by default in the proposals you create.</li>
                            </ul>
                            <p className="approval-note">⏱ All requests require team-leader approval and will appear in orange until processed.</p>
                        </div>
                        <div className="form-section">
                            <label>Team Membership</label>
                            <Select
                                isMulti
                                options={options.teams}
                                value={selectedTeams}
                                onChange={(newTeams) => {
                                    // Prevent removal of inherited teams
                                    const inheritedTeamValues = inheritedSettings.teams || [];
                                    const newTeamsWithInherited = [...newTeams];

                                    // Add back any inherited teams that were removed
                                    inheritedTeamValues.forEach(inheritedTeamId => {
                                        if (!newTeams.some(team => team.value === inheritedTeamId)) {
                                            const inheritedTeam = options.teams.find(team => team.value === inheritedTeamId);
                                            if (inheritedTeam) {
                                                newTeamsWithInherited.push(inheritedTeam);
                                            }
                                        }
                                    });

                                    setSelectedTeams(newTeamsWithInherited);
                                }}
                                className="settings-select"
                                styles={pendingStyles('teams')}
                                placeholder="Select teams to join..."
                                data-testid="user-settings-teams-select"
                            />

                            <p className="field-hint">Orange items are pending team leader approval. </p>
                        </div>


                        <div className="modal-footer">
                            <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
                            <button type="submit" className="save-btn">Save Changes</button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
