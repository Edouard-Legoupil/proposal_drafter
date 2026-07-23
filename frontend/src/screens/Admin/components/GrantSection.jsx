/**
 * GrantSection Component
 * Handles display and management of access grants
 */

import React from 'react';
import CommonButton from '../../../components/CommonButton/CommonButton';

const GrantSection = ({
  grants = [],
  permissionOptions = [],
  showScope = true,
  dataScopeOptions = [],
  grantForm = { subjectType: 'user', subjectId: '', permissions: [], dataScope: 'self' },
  setGrantForm,
  statusMessage = '',
  actionLoading = false,
  onGrant,
  onRevoke,
  users = [],
  options = {},
  emptyMessage = 'No grants'
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (onGrant) {
      onGrant(grantForm);
    }
  };

  return (
    <div className="grant-section">
      <h3>Grants Management</h3>

      {statusMessage && <div className="status-message">{statusMessage}</div>}

      <div className="grants-list">
        {grants.length === 0 ? (
          <p>{emptyMessage}</p>
        ) : (
          <ul>
            {grants.map((grant, index) => (
              <li key={index}>
                {grant.subjectId} - {grant.permissions.join(', ')}
                <button onClick={() => onRevoke(grant)}>Revoke</button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <form onSubmit={handleSubmit} className="grant-form">
        <div>
          <label>Subject Type:</label>
          <select
            value={grantForm.subjectType}
            onChange={(e) => setGrantForm({...grantForm, subjectType: e.target.value})}
          >
            <option value="user">User</option>
            <option value="role">Role</option>
          </select>
        </div>

        <div>
          <label>Subject ID:</label>
          <select
            value={grantForm.subjectId}
            onChange={(e) => setGrantForm({...grantForm, subjectId: e.target.value})}
          >
            <option value="">Select...</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>{user.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label>Permissions:</label>
          <select
            multiple
            value={grantForm.permissions}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions, option => option.value);
              setGrantForm({...grantForm, permissions: selected});
            }}
          >
            {permissionOptions.map(opt => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
        </div>

        {showScope && (
          <div>
            <label>Data Scope:</label>
            <select
              value={grantForm.dataScope}
              onChange={(e) => setGrantForm({...grantForm, dataScope: e.target.value})}
            >
              {dataScopeOptions.map(scope => (
                <option key={scope} value={scope}>{scope}</option>
              ))}
            </select>
          </div>
        )}

        <CommonButton
          type="submit"
          label={actionLoading ? "Saving..." : "Save Grant"}
          disabled={actionLoading}
        />
      </form>
    </div>
  );
};

export default GrantSection;
