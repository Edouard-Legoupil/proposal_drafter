import React from 'react'

export default function GrantTable({ grants, permissionOptions, onRevoke, showScope = true, emptyMessage = 'No access grants yet' }) {
  if (!grants?.length) {
    return <div className="grant-table-empty">{emptyMessage}</div>
  }

  return (
    <table className="grant-table">
      <thead>
        <tr>
          <th>Subject</th>
          <th>Type</th>
          <th>Permissions</th>
          {showScope && <th>Scope</th>}
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {grants.map(grant => (
          <tr key={grant.id || `${grant.subject_type}-${grant.subject_id}`}>
            <td className="grant-subject">{grant.subject_label || grant.subject_name || grant.subject_id}</td>
            <td>{grant.subject_type}</td>
            <td>
              <div className="grant-permissions">
                {permissionOptions
                  .filter(opt => grant.permissions?.includes(opt.key))
                  .map(opt => (
                    <span key={opt.key} className="grant-permission-badge">
                      {opt.label}
                    </span>
                  ))}
              </div>
            </td>
            {showScope && <td>{grant.data_scope || 'self'}</td>}
            <td>
              <button type="button" className="ghost-button" onClick={() => onRevoke(grant.id)}>
                Revoke
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
