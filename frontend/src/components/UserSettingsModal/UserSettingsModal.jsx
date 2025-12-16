import { useState, useEffect } from 'react';
import Select from 'react-select';
import './UserSettingsModal.css';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function UserSettingsModal({ show, onClose }) {
    const [roles, setRoles] = useState([]);
    const [selectedRoles, setSelectedRoles] = useState([]);
    const [donorGroups, setDonorGroups] = useState([]);
    const [selectedDonorGroups, setSelectedDonorGroups] = useState([]);
    const [outcomes, setOutcomes] = useState([]);
    const [selectedOutcomes, setSelectedOutcomes] = useState([]);
    const [geographicCoverageType, setGeographicCoverageType] = useState('global');
    const [geographicCoverageRegion, setGeographicCoverageRegion] = useState('');
    const [geographicCoverageCountry, setGeographicCoverageCountry] = useState('');

    useEffect(() => {
        if (show) {
            async function fetchInitialData() {
                try {
                    const [rolesRes, donorGroupsRes, outcomesRes, settingsRes] = await Promise.all([
                        fetch(`${API_BASE_URL}/roles`),
                        fetch(`${API_BASE_URL}/donors/groups`),
                        fetch(`${API_BASE_URL}/outcomes`),
                        fetch(`${API_BASE_URL}/users/me/settings`)
                    ]);

                    if (rolesRes.ok) {
                        const data = await rolesRes.json();
                        setRoles(data.map(r => ({ value: r.id, label: r.name })));
                    }
                    if (donorGroupsRes.ok) {
                        const data = await donorGroupsRes.json();
                        setDonorGroups(data.donor_groups.map(dg => ({ value: dg, label: dg })));
                    }
                    if (outcomesRes.ok) {
                        const data = await outcomesRes.json();
                        setOutcomes(data.outcomes.map(o => ({ value: o.id, label: o.name })));
                    }
                    if (settingsRes.ok) {
                        const data = await settingsRes.json();
                        setSelectedRoles(roles.filter(r => data.roles.includes(r.value)));
                        setSelectedDonorGroups(donorGroups.filter(dg => data.donor_groups.includes(dg.value)));
                        setSelectedOutcomes(outcomes.filter(o => data.outcomes.includes(o.value)));
                        setGeographicCoverageType(data.geographic_coverage_type);
                        setGeographicCoverageRegion(data.geographic_coverage_region);
                        setGeographicCoverageCountry(data.geographic_coverage_country);
                    }
                } catch (error) {
                    console.error("Failed to fetch initial data:", error);
                }
            }
            fetchInitialData();
        }
    }, [show]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        const settings = {
            geographic_coverage_type: geographicCoverageType,
            geographic_coverage_region: geographicCoverageRegion,
            geographic_coverage_country: geographicCoverageCountry,
            roles: selectedRoles.map(r => r.value),
            donor_groups: selectedDonorGroups.map(dg => dg.value),
            outcomes: selectedOutcomes.map(o => o.value)
        };
        try {
            const response = await fetch(`${API_BASE_URL}/users/me/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            if (response.ok) {
                onClose();
            } else {
                console.error("Failed to update settings");
            }
        } catch (error) {
            console.error("Failed to update settings:", error);
        }
    };

    if (!show) {
        return null;
    }

    return (
        <div className="modal-overlay">
            <div className="modal">
                <h2>User Settings</h2>
                <form onSubmit={handleSubmit}>
                    <label>Roles</label>
                    <Select
                        isMulti
                        options={roles}
                        value={selectedRoles}
                        onChange={setSelectedRoles}
                    />

                    {selectedRoles.some(r => r.label === 'knowledge manager donors') && (
                        <>
                            <label>Donor Groups</label>
                            <Select
                                isMulti
                                options={donorGroups}
                                value={selectedDonorGroups}
                                onChange={setSelectedDonorGroups}
                            />
                        </>
                    )}

                    {selectedRoles.some(r => r.label === 'knowledge manager outcome') && (
                        <>
                            <label>Outcomes</label>
                            <Select
                                isMulti
                                options={outcomes}
                                value={selectedOutcomes}
                                onChange={setSelectedOutcomes}
                            />
                        </>
                    )}

                    <label>Geographic Coverage</label>
                    <select value={geographicCoverageType} onChange={e => setGeographicCoverageType(e.target.value)}>
                        <option value="global">Global</option>
                        <option value="regional">Regional</option>
                        <option value="country">Country</option>
                    </select>

                    {geographicCoverageType === 'regional' && (
                        <input type="text" placeholder="Region" value={geographicCoverageRegion} onChange={e => setGeographicCoverageRegion(e.target.value)} />
                    )}
                    {geographicCoverageType === 'country' && (
                        <input type="text" placeholder="Country" value={geographicCoverageCountry} onChange={e => setGeographicCoverageCountry(e.target.value)} />
                    )}
                    <button type="submit">Save</button>
                    <button type="button" onClick={onClose}>Cancel</button>
                </form>
            </div>
        </div>
    );
}
