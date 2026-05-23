import { useState, useEffect } from 'react';
import Select from 'react-select';
import './UserSettingsModal.css';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

export default function UserSettingsModal({ show, onClose }) {
    const [options, setOptions] = useState({
        roles: [],
        donors: [],
        outcomes: [],
        field_contexts: [],
        teams: []
    });
    const [grantedRoles, setGrantedRoles] = useState([]);
    const [selectedRoles, setSelectedRoles] = useState([]);
    const [selectedDonors, setSelectedDonors] = useState([]);
    const [selectedOutcomes, setSelectedOutcomes] = useState([]);
    const [selectedFieldContexts, setSelectedFieldContexts] = useState([]);
    const [selectedTeams, setSelectedTeams] = useState([]);
    const [pendingRequests, setPendingRequests] = useState({
        roles: [],
        donors: [],
        outcomes: [],
        field_contexts: [],
        teams: []
    });
    const [inheritedSettings, setInheritedSettings] = useState({
        roles: [],
        donors: [],
        outcomes: [],
        field_contexts: [],
        teams: []
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (show) {
            fetchInitialData();
        }
    }, [show]);

    const fetchInitialData = async () => {
        setLoading(true);
        try {
            const [rolesRes, donorsRes, outcomesRes, fieldContextsRes, settingsRes, teamsRes, pendingRes, inheritedRes] = await Promise.all([
                fetch(`${API_BASE_URL}/roles`),
                fetch(`${API_BASE_URL}/donors`),
                fetch(`${API_BASE_URL}/outcomes`),
                fetch(`${API_BASE_URL}/field-contexts`),
                fetch(`${API_BASE_URL}/users/me/settings`, { credentials: 'include' }),
                fetch(`${API_BASE_URL}/teams`),
                fetch(`${API_BASE_URL}/settings/requests/pending`, { credentials: 'include' }),
                fetch(`${API_BASE_URL}/users/me/approved-settings`, { credentials: 'include' })
            ]);

            let rolesData = [];
            let donorsData = [];
            let outcomesData = [];
            let fieldContextsData = [];
            let teamsData = [];

            if (rolesRes.ok) rolesData = await rolesRes.json();
            if (donorsRes.ok) {
                const d = await donorsRes.json();
                donorsData = d.donors || [];
            }
            if (outcomesRes.ok) {
                const o = await outcomesRes.json();
                outcomesData = o.outcomes || [];
            }
            if (fieldContextsRes.ok) {
                const fc = await fieldContextsRes.json();
                fieldContextsData = fc.field_contexts || [];
            }
            if (teamsRes.ok) {
                const t = await teamsRes.json();
                teamsData = t.teams || [];
            }

            const rolesOptions = rolesData.map(r => ({ value: r.id, label: r.name }));
            const dOptions = donorsData.map(d => ({ value: d.id, label: d.name }));
            const outcomeOptions = outcomesData.map(o => ({ value: o.id, label: o.name }));
            const fcOptions = fieldContextsData.map(fc => ({ value: fc.id, label: fc.name }));
            const teamOptions = teamsData.map(t => ({ value: t.id, label: t.name }));

            setOptions({
                roles: rolesOptions,
                donors: dOptions,
                outcomes: outcomeOptions,
                field_contexts: fcOptions,
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
                    if (request.setting_type === 'donor_focal') pendingMap.donors.push(request.setting_value);
                    if (request.setting_type === 'outcome_focal') pendingMap.outcomes.push(request.setting_value);
                    if (request.setting_type === 'field_context_focal') pendingMap.field_contexts.push(request.setting_value);
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
                        if (setting.setting_type === 'donor_focal') inheritedMap.donors.push(setting.setting_value);
                        if (setting.setting_type === 'outcome_focal') inheritedMap.outcomes.push(setting.setting_value);
                        if (setting.setting_type === 'field_context_focal') inheritedMap.field_contexts.push(setting.setting_value);
                        if (setting.setting_type === 'team_membership') inheritedMap.teams.push(setting.setting_value);
                    }
                });
                
                setInheritedSettings(inheritedMap);
            }

            if (settingsRes.ok) {
                const data = await settingsRes.json();
                if (data) {
                    setGrantedRoles(data.roles || []);

                    const allRoleIds = [...(data.roles || []), ...(data.requested_roles || [])];
                    const uniqueRoleIds = [...new Set(allRoleIds)];
                    setSelectedRoles(rolesOptions.filter(r => uniqueRoleIds.includes(r.value)));

                    setSelectedDonors(dOptions.filter(d => (data.donor_ids || []).includes(d.value)));
                    setSelectedOutcomes(outcomeOptions.filter(o => (data.outcomes || []).includes(o.value)));
                    setSelectedFieldContexts(fcOptions.filter(fc => (data.field_contexts || []).includes(fc.value)));
                    setSelectedTeams(teamOptions.filter(t => (data.team_memberships || []).includes(t.value)));
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

        // When saving, we keep existing roles as is, and anything new goes to requested_roles
        // Actually, the backend update_user_settings currently deletes and re-inserts based on what's sent.
        // So we send the current granted roles and the current requested roles (anything selected that is NOT granted).

        const currentSelectedIds = selectedRoles.map(r => r.value);
        const newRequestedRoles = currentSelectedIds.filter(id => !grantedRoles.includes(id));

        const settings = {
            roles: grantedRoles.filter(id => currentSelectedIds.includes(id)), // Keep granted roles that are still selected
            requested_roles: newRequestedRoles,
            donor_ids: selectedDonors.map(d => d.value),
            outcomes: selectedOutcomes.map(o => o.value),
            field_contexts: selectedFieldContexts.map(fc => fc.value),
            team_memberships: selectedTeams.map(t => t.value)
        };

        try {
            const response = await fetch(`${API_BASE_URL}/users/me/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
                credentials: 'include'
            });
            if (response.ok) {
                onClose();
            } else {
                console.error("Failed to update settings");
                alert("Failed to update settings.");
            }
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
                            <h3>Manage Your Access</h3>
                            <p>This form allows you to request additional permissions and manage your focal areas.</p>
                            <ul className="instruction-list">
                                <li><strong>Roles:</strong> Determine what actions you can perform in the system. Requested roles appear in orange until approved.</li>
                                <li><strong>Team Membership:</strong> Join teams to collaborate with others and access team-specific resources.</li>
                                <li><strong>Donor Focal:</strong> Select donors you work with to filter relevant content in proposals and knowledge cards.</li>
                                <li><strong>Outcomes Focal:</strong> Choose outcomes you focus on to streamline your workflow and see relevant information.</li>
                                <li><strong>Field Contexts Focal:</strong> Select countries/regions you work in to filter geographic data and proposals.</li>
                            </ul>
                            <p className="approval-note">⏱ All requests require administrator approval and will appear in orange until processed.</p>
                            <p className="inheritance-note">🔗 Settings marked in green are inherited from your team memberships and cannot be removed directly.</p>
                        </div>
                        <div className="form-section">
                            <label>Team Collaboration</label>
                            <Select
                                isMulti
                                options={options.teams}
                                value={selectedTeams}
                                onChange={setSelectedTeams}
                                className="settings-select"
                                styles={pendingStyles('teams')}
                                placeholder="Select teams to join..."
                            />
                            <p className="field-hint">
                                {selectedTeams.some(t => inheritedSettings.teams.includes(t.value)) ? '✓ Some teams have inherited settings • ' : ''}
                                Join teams to collaborate on proposals and share resources.
                            </p>
                        </div>

                        <div className="form-section">
                            <label>Roles and Permissions</label>
                            <Select
                                isMulti
                                options={options.roles}
                                value={selectedRoles}
                                onChange={setSelectedRoles}
                                styles={roleStyles}
                                className="settings-select"
                                placeholder="Select roles to request..."
                            />
                            <p className="field-hint">Orange items are pending administrator approval. Roles determine system capabilities.</p>
                        </div>

                        <div className="form-section">
                            <label>Donor Focus Areas</label>
                            <Select
                                isMulti
                                options={options.donors}
                                value={selectedDonors}
                                onChange={setSelectedDonors}
                                className="settings-select"
                                styles={pendingStyles('donors')}
                                placeholder="Select donors you focus on..."
                            />
                            <p className="field-hint">Filter proposals and knowledge cards by your selected donors.</p>
                        </div>

                        <div className="form-section">
                            <label>Outcome Specialization</label>
                            <Select
                                isMulti
                                options={options.outcomes}
                                value={selectedOutcomes}
                                onChange={setSelectedOutcomes}
                                className="settings-select"
                                styles={pendingStyles('outcomes')}
                                placeholder="Select outcomes you focus on..."
                            />
                            <p className="field-hint">See only the outcomes relevant to your work.</p>
                        </div>

                        <div className="form-section">
                            <label>Geographic Focus</label>
                            <Select
                                isMulti
                                options={options.field_contexts}
                                value={selectedFieldContexts}
                                onChange={setSelectedFieldContexts}
                                className="settings-select"
                                styles={pendingStyles('field_contexts')}
                                placeholder="Select countries/regions you focus on..."
                            />
                            <p className="field-hint">Filter data by your geographic areas of responsibility.</p>
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
