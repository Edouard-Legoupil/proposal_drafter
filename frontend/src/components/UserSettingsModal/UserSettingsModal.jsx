import { useState, useEffect } from 'react';
import Select from 'react-select';
import './UserSettingsModal.css';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

export default function UserSettingsModal({ show, onClose }) {
    const [options, setOptions] = useState({
        roles: [],
        donors: [],
        outcomes: [],
        field_contexts: []
    });
    const [grantedRoles, setGrantedRoles] = useState([]);
    const [selectedRoles, setSelectedRoles] = useState([]);
    const [selectedDonors, setSelectedDonors] = useState([]);
    const [selectedOutcomes, setSelectedOutcomes] = useState([]);
    const [selectedFieldContexts, setSelectedFieldContexts] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (show) {
            fetchInitialData();
        }
    }, [show]);

    const fetchInitialData = async () => {
        setLoading(true);
        try {
            const [rolesRes, donorsRes, outcomesRes, fieldContextsRes, settingsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/roles`),
                fetch(`${API_BASE_URL}/donors`),
                fetch(`${API_BASE_URL}/outcomes`),
                fetch(`${API_BASE_URL}/field-contexts`),
                fetch(`${API_BASE_URL}/users/me/settings`, { credentials: 'include' })
            ]);

            let rolesData = [];
            let donorsData = [];
            let outcomesData = [];
            let fieldContextsData = [];

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

            const rolesOptions = rolesData.map(r => ({ value: r.id, label: r.name }));
            const dOptions = donorsData.map(d => ({ value: d.id, label: d.name }));
            const outcomeOptions = outcomesData.map(o => ({ value: o.id, label: o.name }));
            const fcOptions = fieldContextsData.map(fc => ({ value: fc.id, label: fc.name }));

            setOptions({
                roles: rolesOptions,
                donors: dOptions,
                outcomes: outcomeOptions,
                field_contexts: fcOptions
            });

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

    if (!show) return null;

    return (
        <div className="user-settings-overlay" onClick={onClose}>
            <div className="user-settings-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Role and Focal Reviewer Preferences</h2>
                    <button className="close-x" onClick={onClose}>&times;</button>
                </div>

                {loading ? (
                    <div className="modal-loading">Loading settings...</div>
                ) : (
                    <form onSubmit={handleSubmit} className="modal-form">
                        <div className="form-section">
                            <label>Request Role</label>
                            <Select
                                isMulti
                                options={options.roles}
                                value={selectedRoles}
                                onChange={setSelectedRoles}
                                styles={roleStyles}
                                className="settings-select"
                                placeholder="Select roles to request..."
                            />
                            <p className="field-hint">Roles in orange are pending administrator approval.</p>
                        </div>

                        <div className="form-section">
                            <label>Donor Focal</label>
                            <Select
                                isMulti
                                options={options.donors}
                                value={selectedDonors}
                                onChange={setSelectedDonors}
                                className="settings-select"
                                placeholder="Select donors you focus on..."
                            />
                        </div>

                        <div className="form-section">
                            <label>Outcomes Focal</label>
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
                            <label>Field Contexts Focal</label>
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
