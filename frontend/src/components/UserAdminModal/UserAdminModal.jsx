import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import './UserAdminModal.css';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function UserAdminModal({ show, onClose }) {
    const [users, setUsers] = useState([]);
    const [options, setOptions] = useState({
        roles: [],
        donor_groups: [],
        outcomes: [],
        field_contexts: []
    });
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (show) {
            fetchData();
        }
    }, [show]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [usersRes, optionsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/admin/users`, { credentials: 'include' }),
                fetch(`${API_BASE_URL}/admin/options`, { credentials: 'include' })
            ]);

            if (usersRes.ok && optionsRes.ok) {
                const usersData = await usersRes.json();
                const optionsData = await optionsRes.json();
                setUsers(usersData || []);
                setOptions({
                    roles: (optionsData.roles || []).map(r => ({ value: r.id, label: r.name })),
                    donor_groups: (optionsData.donor_groups || []).map(dg => ({ value: dg, label: dg })),
                    outcomes: (optionsData.outcomes || []).map(o => ({ value: o.id, label: o.name })),
                    field_contexts: (optionsData.field_contexts || []).map(fc => ({ value: fc.id, label: fc.name }))
                });
            } else {
                setError("Failed to fetch admin data. Are you sure you are an admin?");
            }
        } catch (err) {
            setError("An error occurred while fetching data.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSettingChange = async (userId, type, selectedOptions) => {
        const user = users.find(u => u.id === userId);
        if (!user) return;

        // Prepare the payload based on all current settings for this user
        const payload = {
            role_ids: type === 'roles' ? (selectedOptions || []).map(o => o.value) : (user.roles || []).map(r => r.id),
            donor_groups: type === 'donor_groups' ? (selectedOptions || []).map(o => o.value) : (user.donor_groups || []),
            outcomes: type === 'outcomes' ? (selectedOptions || []).map(o => o.value) : (user.outcomes || []),
            field_contexts: type === 'field_contexts' ? (selectedOptions || []).map(o => o.value) : (user.field_contexts || [])
        };

        try {
            const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                credentials: 'include'
            });

            if (response.ok) {
                // Update local state
                setUsers(users.map(u => {
                    if (u.id === userId) {
                        const updated = { ...u };
                        if (type === 'roles') updated.roles = selectedOptions.map(o => ({ id: o.value, name: o.label }));
                        if (type === 'donor_groups') updated.donor_groups = selectedOptions.map(o => o.value);
                        if (type === 'outcomes') updated.outcomes = selectedOptions.map(o => o.value);
                        if (type === 'field_contexts') updated.field_contexts = selectedOptions.map(o => o.value);
                        return updated;
                    }
                    return u;
                }));
            } else {
                alert("Failed to update user settings.");
            }
        } catch (err) {
            console.error(err);
            alert("An error occurred while updating settings.");
        }
    };

    if (!show) return null;

    const filteredUsers = users.filter(user =>
        (user.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
        (user.email?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
        (user.team_name?.toLowerCase() || '').includes(searchTerm.toLowerCase())
    );

    return (
        <div className="admin-modal-overlay" onClick={onClose}>
            <div className="admin-modal-content" onClick={e => e.stopPropagation()}>
                <div className="admin-modal-header">
                    <h2>System Administration</h2>
                    <button className="close-button" onClick={onClose}>&times;</button>
                </div>

                <div className="admin-modal-body">
                    <div className="search-bar">
                        <input
                            type="text"
                            placeholder="Search users by name, email or team..."
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                        />
                    </div>

                    {loading ? (
                        <div className="admin-loading">Loading users...</div>
                    ) : error ? (
                        <div className="admin-error">{error}</div>
                    ) : (
                        <div className="users-table-container">
                            <table className="users-table">
                                <thead>
                                    <tr>
                                        <th>User</th>
                                        <th>Roles</th>
                                        <th>Donor Groups</th>
                                        <th>Outcomes</th>
                                        <th>Field Contexts</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredUsers.map(user => (
                                        <tr key={user.id}>
                                            <td>
                                                <div className="user-info">
                                                    <span className="user-name">{user.name}</span>
                                                    <span className="user-email">{user.email}</span>
                                                    <span className="user-team">{user.team_name || 'No Team'}</span>
                                                </div>
                                            </td>
                                            <td>
                                                <Select
                                                    isMulti
                                                    options={options.roles}
                                                    value={(user.roles || []).map(r => ({ value: r.id, label: r.name }))}
                                                    onChange={(selected) => handleSettingChange(user.id, 'roles', selected)}
                                                    className="admin-select"
                                                    placeholder="Roles..."
                                                />
                                            </td>
                                            <td>
                                                <Select
                                                    isMulti
                                                    options={options.donor_groups}
                                                    value={(user.donor_groups || []).map(dg => ({ value: dg, label: dg }))}
                                                    onChange={(selected) => handleSettingChange(user.id, 'donor_groups', selected)}
                                                    className="admin-select"
                                                    placeholder="Donors..."
                                                />
                                            </td>
                                            <td>
                                                <Select
                                                    isMulti
                                                    options={options.outcomes}
                                                    value={(user.outcomes || []).map(oid => {
                                                        const opt = options.outcomes.find(o => o.value === oid);
                                                        return opt || { value: oid, label: oid };
                                                    })}
                                                    onChange={(selected) => handleSettingChange(user.id, 'outcomes', selected)}
                                                    className="admin-select"
                                                    placeholder="Outcomes..."
                                                />
                                            </td>
                                            <td>
                                                <Select
                                                    isMulti
                                                    options={options.field_contexts}
                                                    value={(user.field_contexts || []).map(fcid => {
                                                        const opt = options.field_contexts.find(fc => fc.value === fcid);
                                                        return opt || { value: fcid, label: fcid };
                                                    })}
                                                    onChange={(selected) => handleSettingChange(user.id, 'field_contexts', selected)}
                                                    className="admin-select"
                                                    placeholder="Field Contexts..."
                                                />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                <div className="admin-modal-footer">
                    <button className="primary-button" onClick={onClose}>Close</button>
                </div>
            </div>
        </div>
    );
}
