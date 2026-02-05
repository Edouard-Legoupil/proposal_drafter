import { useState, useEffect } from 'react';
import Select from 'react-select';
import './UserSettingsModal.css';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function UserSettingsModal({ show, onClose }) {
    const [options, setOptions] = useState({
        roles: [],
        donor_groups: [],
        outcomes: [],
        field_contexts: []
    });
    const [selectedRoles, setSelectedRoles] = useState([]);
    const [selectedDonorGroups, setSelectedDonorGroups] = useState([]);
    const [selectedOutcomes, setSelectedOutcomes] = useState([]);
    const [selectedFieldContexts, setSelectedFieldContexts] = useState([]);
    const [geographicCoverageType, setGeographicCoverageType] = useState('global');
    const [geographicCoverageRegion, setGeographicCoverageRegion] = useState('');
    const [geographicCoverageCountry, setGeographicCoverageCountry] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (show) {
            fetchInitialData();
        }
    }, [show]);

    const fetchInitialData = async () => {
        setLoading(true);
        try {
            const [rolesRes, donorGroupsRes, outcomesRes, fieldContextsRes, settingsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/roles`),
                fetch(`${API_BASE_URL}/donors/groups`),
                fetch(`${API_BASE_URL}/outcomes`),
                fetch(`${API_BASE_URL}/admin/options`), // Re-using admin/options for field contexts or assuming there's a /field-contexts
                fetch(`${API_BASE_URL}/users/me/settings`, { credentials: 'include' })
            ]);

            let rolesData = [];
            let donorGroupsData = [];
            let outcomesData = [];
            let fieldContextsData = [];

            if (rolesRes.ok) rolesData = await rolesRes.json();
            if (donorGroupsRes.ok) {
                const dg = await donorGroupsRes.json();
                donorGroupsData = dg.donor_groups || [];
            }
            if (outcomesRes.ok) {
                const o = await outcomesRes.json();
                outcomesData = o.outcomes || [];
            }
            // Fallback for field contexts if the admin/options endpoint is accessible
            if (fieldContextsRes.ok) {
                const fc = await fieldContextsRes.json();
                fieldContextsData = fc.field_contexts || [];
            }

            const rolesOptions = rolesData.map(r => ({ value: r.id, label: r.name }));
            const dgOptions = donorGroupsData.map(dg => ({ value: dg, label: dg }));
            const outcomeOptions = outcomesData.map(o => ({ value: o.id, label: o.name }));
            const fcOptions = fieldContextsData.map(fc => ({ value: fc.id, label: fc.name }));

            setOptions({
                roles: rolesOptions,
                donor_groups: dgOptions,
                outcomes: outcomeOptions,
                field_contexts: fcOptions
            });

            if (settingsRes.ok) {
                const data = await settingsRes.json();
                if (data) {
                    setSelectedRoles(rolesOptions.filter(r => (data.roles || []).includes(r.value)));
                    setSelectedDonorGroups(dgOptions.filter(dg => (data.donor_groups || []).includes(dg.value)));
                    setSelectedOutcomes(outcomeOptions.filter(o => (data.outcomes || []).includes(o.value)));
                    setSelectedFieldContexts(fcOptions.filter(fc => (data.field_contexts || []).includes(fc.value)));
                    setGeographicCoverageType(data.geographic_coverage_type || 'global');
                    setGeographicCoverageRegion(data.geographic_coverage_region || '');
                    setGeographicCoverageCountry(data.geographic_coverage_country || '');
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
        const settings = {
            geographic_coverage_type: geographicCoverageType,
            geographic_coverage_region: geographicCoverageRegion,
            geographic_coverage_country: geographicCoverageCountry,
            roles: selectedRoles.map(r => r.value),
            donor_groups: selectedDonorGroups.map(dg => dg.value),
            outcomes: selectedOutcomes.map(o => o.value),
            field_contexts: selectedFieldContexts.map(fc => fc.value)
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

    if (!show) return null;

    return (
        <div className="user-settings-overlay" onClick={onClose}>
            <div className="user-settings-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>My Profile & Preferences</h2>
                    <button className="close-x" onClick={onClose}>&times;</button>
                </div>

                {loading ? (
                    <div className="modal-loading">Loading settings...</div>
                ) : (
                    <form onSubmit={handleSubmit} className="modal-form">
                        <div className="form-section">
                            <label>Assigned Roles (View Only)</label>
                            <Select
                                isMulti
                                options={options.roles}
                                value={selectedRoles}
                                isDisabled={true}
                                className="settings-select"
                            />
                            <p className="field-hint">Roles are managed by system administrators.</p>
                        </div>

                        <div className="form-section">
                            <label>Geographic Coverage</label>
                            <div className="coverage-controls">
                                <select value={geographicCoverageType} onChange={e => setGeographicCoverageType(e.target.value)}>
                                    <option value="global">Global</option>
                                    <option value="regional">Regional</option>
                                    <option value="country">One Country Operation</option>
                                </select>

                                {geographicCoverageType === 'regional' && (
                                    <input type="text" placeholder="Specify Region..." value={geographicCoverageRegion} onChange={e => setGeographicCoverageRegion(e.target.value)} />
                                )}
                                {geographicCoverageType === 'country' && (
                                    <input type="text" placeholder="Specify Country..." value={geographicCoverageCountry} onChange={e => setGeographicCoverageCountry(e.target.value)} />
                                )}
                            </div>
                        </div>

                        <div className="form-section">
                            <label>My Preferred Donor Groups</label>
                            <Select
                                isMulti
                                options={options.donor_groups}
                                value={selectedDonorGroups}
                                onChange={setSelectedDonorGroups}
                                className="settings-select"
                                placeholder="Select donors you focus on..."
                            />
                        </div>

                        <div className="form-section">
                            <label>My Preferred Outcomes</label>
                            <Select
                                isMulti
                                options={options.outcomes}
                                value={selectedOutcomes}
                                onChange={setSelectedOutcomes}
                                className="settings-select"
                                placeholder="Select outcomes you focus on..."
                            />
                        </div>

                        <div className="form-section">
                            <label>My Preferred Field Contexts</label>
                            <Select
                                isMulti
                                options={options.field_contexts}
                                value={selectedFieldContexts}
                                onChange={setSelectedFieldContexts}
                                className="settings-select"
                                placeholder="Select countries/regions you focus on..."
                            />
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
