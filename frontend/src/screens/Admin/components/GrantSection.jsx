/**
 * GrantSection Component
 * Handles display and management of access grants
 */

import React from 'react'
import CommonButton from '../../../components/CommonButton/CommonButton'
import SubjectPicker from './SubjectPicker'

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
  const subjectTypeOptions = [
    { value: 'user', label: 'User' },
    { value: 'team', label: 'Team' },
    { value: 'role', label: 'Role' },
    { value: 'donor_group', label: 'Donor Group' }
  ]

  const handleSubmit = (event) => {
    if (onGrant) onGrant(event)
  }

  return (
    <div className="grant-section">
      <h3>Grant Access</h3>

      {statusMessage && <div className="status-message">{statusMessage}</div>}

      <div className="grants-list">
        {grants.length === 0 ? (
          <p>{emptyMessage}</p>
        ) : (
          <ul>
            {grants.map((grant, index) => (
              <li key={grant.id || index}>
                {grant.subject_name || grant.subjectName || grant.subject_id || grant.subjectId}
                {' — '}
                {(grant.permissions || []).join(', ')}
                <button type="button" onClick={() => onRevoke?.(grant.id)}>Revoke</button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <form onSubmit={handleSubmit} className="grant-form">
        <div>
          <label htmlFor="grant-subject-type">Subject type</label>
          <select
            id="grant-subject-type"
            value={grantForm.subjectType}
            onChange={(e) => setGrantForm({ ...grantForm, subjectType: e.target.value, subjectId: '' })}
          >
            {subjectTypeOptions.map(subjectType => (
              <option key={subjectType.value} value={subjectType.value}>{subjectType.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="grant-subject">Select a user or team</label>
          <SubjectPicker
            className="admin-select"
            subjectType={grantForm.subjectType}
            value={grantForm.subjectId}
            onChange={(subjectId) => setGrantForm({ ...grantForm, subjectId })}
            users={users}
            options={options}
          />
        </div>

        <div>
          <label htmlFor="grant-permissions">Permissions</label>
          <select
            id="grant-permissions"
            multiple
            value={grantForm.permissions}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions, option => option.value)
              setGrantForm({ ...grantForm, permissions: selected })
            }}
          >
            {permissionOptions.map(opt => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
        </div>

        {showScope && (
          <div>
            <label htmlFor="grant-data-scope">Data scope</label>
            <select
              id="grant-data-scope"
              value={grantForm.dataScope}
              onChange={(e) => setGrantForm({ ...grantForm, dataScope: e.target.value })}
            >
              {dataScopeOptions.map(scope => (
                <option key={scope} value={scope}>{scope}</option>
              ))}
            </select>
          </div>
        )}

        <CommonButton
          type="submit"
          label={actionLoading ? 'Saving…' : 'Save Grant'}
          disabled={actionLoading}
        />
      </form>
    </div>
  );
}

export default GrantSection
