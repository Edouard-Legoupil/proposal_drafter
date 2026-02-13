import React, { useState, useEffect } from 'react';
import './RoleRequestModal.css';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api";

export default function RoleRequestModal({ show, onClose, onSuccess }) {
    const [roles, setRoles] = useState([]);
    const [selectedRole, setSelectedRole] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (show) {
            fetchRoles();
        }
    }, [show]);

    const fetchRoles = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/roles`);
            if (response.ok) {
                const data = await response.json();
                // Filter out 'proposal writer' as it's the default
                setRoles(data.filter(r => r.name !== 'proposal writer'));
            }
        } catch (err) {
            console.error("Failed to fetch roles", err);
        }
    };

    const handleSubmit = async () => {
        if (!selectedRole) return;
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/request-role`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role_id: selectedRole }),
                credentials: 'include'
            });

            if (response.ok) {
                onSuccess();
                onClose();
            } else {
                setError("Failed to submit request.");
            }
        } catch (err) {
            setError("An error occurred.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (!show) return null;

    return (
        <div className="role-modal-overlay" onClick={onClose}>
            <div className="role-modal-content" onClick={e => e.stopPropagation()}>
                <div className="role-modal-header">
                    <h2>Request Elevated Access</h2>
                    <button className="close-button" onClick={onClose}>&times;</button>
                </div>
                <div className="role-modal-body">
                    <p>Select a role to request additional permissions.</p>
                    <select
                        value={selectedRole}
                        onChange={e => setSelectedRole(e.target.value)}
                        className="role-select"
                    >
                        <option value="">Select a role...</option>
                        {roles.map(role => (
                            <option key={role.id} value={role.id}>{role.name}</option>
                        ))}
                    </select>
                    {error && <div className="error-message">{error}</div>}
                </div>
                <div className="role-modal-footer">
                    <button className="secondary-button" onClick={onClose}>Cancel</button>
                    <button
                        className="primary-button"
                        onClick={handleSubmit}
                        disabled={!selectedRole || loading}
                    >
                        {loading ? 'Submitting...' : 'Submit Request'}
                    </button>
                </div>
            </div>
        </div>
    );
}
