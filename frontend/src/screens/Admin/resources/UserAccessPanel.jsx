import React, { useState, useEffect, useMemo } from 'react'
import Select from 'react-select'
import '../../../components/UserAdminModal/UserAdminModal.css'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

export default function UserAccessPanel({ resourceId }) {
  const [users, setUsers] = useState([])
  const [options, setOptions] = useState({
    roles: [], donor_groups: [], outcomes: [], field_contexts: [], teams: [], template_requests: []
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [newTeamName, setNewTeamName] = useState('')
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [bulkAction, setBulkAction] = useState('')
  const [bulkValue, setBulkValue] = useState(null)
  const [bulkLoading, setBulkLoading] = useState(false)
  const [roleRequests, setRoleRequests] = useState([])
  const [settingsRequests, setSettingsRequests] = useState([])
  const [showRoleRequestModal, setShowRoleRequestModal] = useState(false)
  const [showSettingsRequestModal, setShowSettingsRequestModal] = useState(false)
  const [selectedRequest, setSelectedRequest] = useState(null)
  const [approvalNote, setApprovalNote] = useState('')
  const [processingRequest, setProcessingRequest] = useState(false)

  useEffect(() => {
    fetchData()
    fetchRoleRequests()
    fetchSettingsRequests()
  }, [])

  const fetchRoleRequests = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/role-requests`, {
        credentials: 'include'
      })
      if (res.ok) {
        setRoleRequests(await res.json())
      }
    } catch (err) {
      console.error('Failed to fetch role requests:', err)
    }
  }

  const fetchSettingsRequests = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/settings-requests`, {
        credentials: 'include'
      })
      if (res.ok) {
        setSettingsRequests(await res.json())
      }
    } catch (err) {
      console.error('Failed to fetch settings requests:', err)
    }
  }

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [usersRes, optionsRes, requestsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/admin/users`, { credentials: 'include' }),
        fetch(`${API_BASE_URL}/admin/options`, { credentials: 'include' }),
        fetch(`${API_BASE_URL}/admin/template-requests`, { credentials: 'include' })
      ])
      if (usersRes.ok && optionsRes.ok) {
        const usersData = await usersRes.json()
        const optionsData = await optionsRes.json()
        setUsers(usersData || [])
        setOptions({
          roles: (optionsData.roles || []).map(r => ({ value: r.id, label: r.name })),
          donor_groups: (optionsData.donor_groups || []).map(dg => ({ value: dg, label: dg })),
          outcomes: (optionsData.outcomes || []).map(o => ({ value: o.id, label: o.name })),
          field_contexts: (optionsData.field_contexts || []).map(fc => ({ value: fc.id, label: fc.name })),
          teams: (optionsData.teams || []).map(t => ({ value: t.id, label: t.name })),
          template_requests: (await requestsRes.json()) || []
        })
      } else {
        setError("Failed to fetch admin data. Are you sure you are an admin?")
      }
    } catch (err) {
      console.error(err)
      setError("An error occurred while fetching data.")
    } finally {
      setLoading(false)
    }
  }

  const requestTypeToField = (settingType) => {
    const mapping = {
      'donor_focal': 'donor_groups',
      'outcome_focal': 'outcomes',
      'field_context_focal': 'field_contexts'
    }
    return mapping[settingType] || settingType
  }

  const stats = useMemo(() => ({
    totalUsers: users.length,
    totalTeams: options.teams.length,
    pendingRequests: users.filter(u => u.requested_role_id).length,
    pendingTemplates: options.template_requests.filter(r => r.status === 'pending').length,
    pendingSettings: settingsRequests.length
  }), [users, options, settingsRequests])

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return
    try {
      const response = await fetch(`${API_BASE_URL}/admin/teams`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newTeamName }), credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setOptions(prev => ({
          ...prev,
          teams: [...prev.teams, { value: data.team.id, label: data.team.name }].sort((a, b) => a.label.localeCompare(b.label))
        }))
        setNewTeamName('')
      } else {
        const data = await response.json()
        alert(data.detail || "Failed to create team.")
      }
    } catch (err) { alert("Error creating team.") }
  }

  const handleUpdateUserTeam = async (userId, selectedOption) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/team`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team_id: selectedOption.value }), credentials: 'include'
      })
      if (response.ok) {
        setUsers(users.map(u => u.id === userId ? { ...u, team_name: selectedOption.label, team_id: selectedOption.value } : u))
      } else { alert("Failed to update user team.") }
    } catch (err) { alert("Error updating user team.") }
  }

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to delete this user? This action cannot be undone.")) return
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, { method: 'DELETE', credentials: 'include' })
      if (response.ok) { setUsers(users.filter(u => u.id !== userId)); setSelectedIds(prev => { const n = new Set(prev); n.delete(userId); return n }) }
      else { alert("Failed to delete user.") }
    } catch (err) { alert("Error deleting user.") }
  }

  const handleSettingChange = async (userId, type, selectedOptions) => {
    const user = users.find(u => u.id === userId)
    if (!user) return

    const selectedValues = selectedOptions.map(o => o.value)

    // Get current user data
    const currentApproved = user[type] || []
    const currentRequested = user[`${type}_requested`] || []

    // Determine what's being added/removed
    const added = selectedValues.filter(v => !currentApproved.includes(v) && !currentRequested.includes(v))
    const removed = currentApproved.filter(v => !selectedValues.includes(v))

    try {
      // Prepare the updated settings for the user
      const updatedSettings = {
        role_ids: (user.roles || []).filter(r => r?.id).map(r => r.id),
        donor_groups: type === 'donor_groups' ? selectedValues : (user.donor_groups || []),
        outcomes: type === 'outcomes' ? selectedValues : (user.outcomes || []),
        field_contexts: type === 'field_contexts' ? selectedValues : (user.field_contexts || [])
      }

      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedSettings),
        credentials: 'include'
      })

      if (response.ok) {
        // Update UI to reflect the changes
        setUsers(users.map(u => {
          if (u.id === userId) {
            return {
              ...u,
              [type]: selectedValues,
              [`${type}_requested`]: [] // Clear any pending requests for this type
            }
          }
          return u
        }))
      } else {
        const errorData = await response.json()
        console.error(`Error updating ${type}:`, errorData.detail || 'Unknown error')
        alert(`Failed to update ${type}: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error(`Error updating ${type} access:`, err)
      alert(`Error updating ${type} access`)
    }
  }

  const handleDownloadTemplate = (request) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(request.initial_file_content, null, 2))
    const a = document.createElement('a')
    a.setAttribute("href", dataStr)
    a.setAttribute("download", `${request.name.replace(/\s+/g, '_')}_template.json`)
    document.body.appendChild(a); a.click(); a.remove()
  }

  const handleApproveRoleRequest = async () => {
    if (!selectedRequest || processingRequest) return

    setProcessingRequest(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/role-requests/${selectedRequest.user_id}/approve?admin_note=${encodeURIComponent(approvalNote)}`, {
        method: 'POST',
        credentials: 'include'
      })

      if (res.ok) {
        const result = await res.json()
        // Update the user in the list to remove the pending request
        setUsers(users.map(u =>
          u.id === selectedRequest.user_id
            ? { ...u, requested_role_id: null, requested_role_name: null }
            : u
        ))
        // Remove from role requests
        setRoleRequests(roleRequests.filter(r => r.user_id !== selectedRequest.user_id))
        setShowRoleRequestModal(false)
        setApprovalNote('')
        // Show success message
        alert(`Role request approved for ${result.user_name}`)
      } else {
        const errorData = await res.json()
        alert(`Failed to approve role request: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error approving role request:', err)
      alert('Error approving role request')
    } finally {
      setProcessingRequest(false)
    }
  }

  const handleRejectRoleRequest = async () => {
    if (!selectedRequest || processingRequest) return

    setProcessingRequest(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/role-requests/${selectedRequest.user_id}/reject?admin_note=${encodeURIComponent(approvalNote)}`, {
        method: 'POST',
        credentials: 'include'
      })

      if (res.ok) {
        const result = await res.json()
        // Update the user in the list to remove the pending request
        setUsers(users.map(u =>
          u.id === selectedRequest.user_id
            ? { ...u, requested_role_id: null, requested_role_name: null }
            : u
        ))
        // Remove from role requests
        setRoleRequests(roleRequests.filter(r => r.user_id !== selectedRequest.user_id))
        setShowRoleRequestModal(false)
        setApprovalNote('')
        // Show success message
        alert(`Role request rejected for ${result.user_name}`)
      } else {
        const errorData = await res.json()
        alert(`Failed to reject role request: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error rejecting role request:', err)
      alert('Error rejecting role request')
    } finally {
      setProcessingRequest(false)
    }
  }

  const handleApproveSettingsRequest = async () => {
    if (!selectedRequest || processingRequest) return

    setProcessingRequest(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/settings-requests/${selectedRequest.request_id}/approve?admin_note=${encodeURIComponent(approvalNote)}`, {
        method: 'POST',
        credentials: 'include'
      })

      if (res.ok) {
        const result = await res.json()
        // Update the user in the list
        const fieldName = requestTypeToField(result.setting_type)
        setUsers(users.map(u => {
          if (u.id === result.user_id) {
            return {
              ...u,
              [fieldName]: [...(u[fieldName] || []), result.setting_value],
              [`${fieldName}_requested`]: (u[`${fieldName}_requested`] || []).filter(v => v !== result.setting_value)
            }
          }
          return u
        }))
        // Remove from settings requests
        setSettingsRequests(settingsRequests.filter(r => r.request_id !== selectedRequest.request_id))
        setShowSettingsRequestModal(false)
        setApprovalNote('')
        // Show success message
        alert(`Settings request approved for ${result.user_name}`)
      } else {
        const errorData = await res.json()
        alert(`Failed to approve settings request: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error approving settings request:', err)
      alert('Error approving settings request')
    } finally {
      setProcessingRequest(false)
    }
  }

  const handleRejectSettingsRequest = async () => {
    if (!selectedRequest || processingRequest) return

    setProcessingRequest(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/settings-requests/${selectedRequest.request_id}/reject?admin_note=${encodeURIComponent(approvalNote)}`, {
        method: 'POST',
        credentials: 'include'
      })

      if (res.ok) {
        const result = await res.json()
        // Update the user in the list to remove the pending request
        const fieldName = requestTypeToField(result.setting_type)
        setUsers(users.map(u => {
          if (u.id === result.user_id) {
            return {
              ...u,
              [`${fieldName}_requested`]: (u[`${fieldName}_requested`] || []).filter(v => v !== result.setting_value)
            }
          }
          return u
        }))
        // Remove from settings requests
        setSettingsRequests(settingsRequests.filter(r => r.request_id !== selectedRequest.request_id))
        setShowSettingsRequestModal(false)
        setApprovalNote('')
        // Show success message
        alert(`Settings request rejected for ${result.user_name}`)
      } else {
        const errorData = await res.json()
        alert(`Failed to reject settings request: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error rejecting settings request:', err)
      alert('Error rejecting settings request')
    } finally {
      setProcessingRequest(false)
    }
  }

  // Bulk actions
  const toggleSelect = (userId) => {
    setSelectedIds(prev => {
      const n = new Set(prev)
      n.has(userId) ? n.delete(userId) : n.add(userId)
      return n
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredUsers.length) { setSelectedIds(new Set()) }
    else { setSelectedIds(new Set(filteredUsers.map(u => u.id))) }
  }

  const handleBulkApply = async () => {
    if (!bulkAction || !bulkValue) return
    const ids = Array.from(selectedIds)
    if (!ids.length) return
    if (!window.confirm(`Apply "${bulkAction}" to ${ids.length} user(s)?`)) return
    setBulkLoading(true)
    try {
      if (bulkAction === 'team') {
        await Promise.allSettled(ids.map(id =>
          fetch(`${API_BASE_URL}/admin/users/${id}/team`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team_id: bulkValue.value }), credentials: 'include'
          })
        ))
        setUsers(prev => prev.map(u => ids.includes(u.id) ? { ...u, team_name: bulkValue.label, team_id: bulkValue.value } : u))
      } else if (bulkAction === 'role') {
        await Promise.allSettled(ids.map(id => {
          const user = users.find(u => u.id === id)
          const existingRoleIds = (user?.roles || []).filter(r => r?.id).map(r => r.id)
          const newRoleIds = [...new Set([...existingRoleIds, bulkValue.value])]
          return fetch(`${API_BASE_URL}/admin/users/${id}/settings`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              role_ids: newRoleIds,
              donor_groups: user?.donor_groups || [],
              outcomes: user?.outcomes || [],
              field_contexts: user?.field_contexts || []
            }), credentials: 'include'
          })
        }))
        await fetchData()
      } else if (bulkAction === 'delete') {
        await Promise.allSettled(ids.map(id =>
          fetch(`${API_BASE_URL}/admin/users/${id}`, { method: 'DELETE', credentials: 'include' })
        ))
        setUsers(prev => prev.filter(u => !ids.includes(u.id)))
      }
      setSelectedIds(new Set())
      setBulkAction('')
      setBulkValue(null)
    } catch (err) { alert('Some bulk operations failed.') }
    finally { setBulkLoading(false) }
  }

  const filteredUsers = users.filter(user =>
    (user.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (user.email?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (user.team_name?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  )

  return (
    <>
      <header className="section-header">
        <h2>User Access Management</h2>
        <p className="section-subtitle">Manage users, teams, roles, and access settings</p>
      </header>

      {/* Summary stat cards */}
      <div className="admin-stats-row">
        <div className="admin-stat-card">
          <span className="stat-value">{stats.totalUsers}</span>
          <span className="stat-label">Total Users</span>
        </div>
        <div className="admin-stat-card">
          <span className="stat-value">{stats.totalTeams}</span>
          <span className="stat-label">Teams</span>
        </div>
        <div className="admin-stat-card accent">
          <span className="stat-value">{stats.pendingRequests}</span>
          <span className="stat-label">Pending Role Requests</span>
        </div>
        <div className="admin-stat-card accent">
          <span className="stat-value">{stats.pendingSettings}</span>
          <span className="stat-label">Pending Settings Requests</span>
        </div>
        <div className="admin-stat-card accent">
          <span className="stat-value">{stats.pendingTemplates}</span>
          <span className="stat-label">Pending Template Requests</span>
        </div>
      </div>

      <div className="admin-modal-body">
        <div className="admin-controls">
          <div className="search-bar">
            <input type="text" placeholder="Search users by name, email or team…" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
          </div>
          <div className="create-team-container">
            <input type="text" placeholder="New Team Name" value={newTeamName} onChange={e => setNewTeamName(e.target.value)} className="create-team-input" />
            <button className="primary-button small" onClick={handleCreateTeam} disabled={!newTeamName.trim()}>
              <i className="fa-solid fa-plus"></i> Create Team
            </button>
          </div>
        </div>

        {/* Bulk action toolbar */}
        {selectedIds.size > 0 && (
          <div className="bulk-toolbar">
            <span className="bulk-count">{selectedIds.size} selected</span>
            <select value={bulkAction} onChange={e => { setBulkAction(e.target.value); setBulkValue(null) }}>
              <option value="">Bulk action…</option>
              <option value="team">Set Team</option>
              <option value="role">Add Role</option>
              <option value="delete">Delete Selected</option>
            </select>
            {bulkAction === 'team' && (
              <Select options={options.teams} value={bulkValue} onChange={setBulkValue} placeholder="Select team…" className="admin-select bulk-select" menuPortalTarget={document.body} />
            )}
            {bulkAction === 'role' && (
              <Select options={options.roles} value={bulkValue} onChange={setBulkValue} placeholder="Select role…" className="admin-select bulk-select" menuPortalTarget={document.body} />
            )}
            {bulkAction === 'delete' && <span className="bulk-warning">⚠ This will permanently delete selected users</span>}
            <button className="primary-button small" disabled={bulkLoading || (!bulkValue && bulkAction !== 'delete')} onClick={handleBulkApply}>
              {bulkLoading ? 'Applying…' : 'Apply'}
            </button>
            <button className="ghost-button small" onClick={() => { setSelectedIds(new Set()); setBulkAction('') }}>Cancel</button>
          </div>
        )}

        {options.template_requests.some(r => r.status === 'pending') && (
          <div className="admin-notification alert">
            <i className="fa-solid fa-file-circle-exclamation"></i>
            <strong>New Template Requests:</strong> {options.template_requests.filter(r => r.status === 'pending').length} requests are awaiting review.
          </div>
        )}

        {users.some(u => u.requested_role_id) && (
          <div className="admin-notification">
            <i className="fa-solid fa-bell"></i>
            <strong>Pending Role Requests:</strong> {users.filter(u => u.requested_role_id).length} users are requesting elevated access.
          </div>
        )}

        {settingsRequests.length > 0 && (
          <div className="admin-notification">
            <i className="fa-solid fa-cog"></i>
            <strong>Pending Settings Requests:</strong> {settingsRequests.length} settings requests are awaiting review.
          </div>
        )}

        {loading ? (
          <div className="admin-loading">Loading users…</div>
        ) : error ? (
          <div className="admin-error">{error}</div>
        ) : (
          <div className="users-table-container">
            <table className="users-table">
              <thead>
                <tr>
                  <th style={{ width: 40 }}>
                    <input type="checkbox" checked={selectedIds.size === filteredUsers.length && filteredUsers.length > 0} onChange={toggleSelectAll} />
                  </th>
                  <th>User</th>
                  <th>Team</th>
                  <th>Roles</th>
                  <th>Donor Groups</th>
                  <th>Outcomes</th>
                  <th>Field Contexts</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map(user => (
                  <tr key={user.id} className={`${user.requested_role_id ? 'row-highlight' : ''} ${selectedIds.has(user.id) ? 'row-selected' : ''}`}>
                    <td>
                      <input type="checkbox" checked={selectedIds.has(user.id)} onChange={() => toggleSelect(user.id)} />
                    </td>
                    <td>
                      <div className="user-info">
                        <span className="user-name">
                          {user.name}
                          {user.requested_role_id && (
                            <span className="request-badge" title={`Requested: ${user.requested_role_name}`}>
                              Pending: {user.requested_role_name}
                            </span>
                          )}
                        </span>
                        <span className="user-email">{user.email}</span>
                      </div>
                    </td>
                    <td>
                      <Select
                        options={options.teams}
                        value={options.teams.find(t => t.label === user.team_name) || { label: user.team_name || 'Select Team', value: user.team_id }}
                        onChange={selected => handleUpdateUserTeam(user.id, selected)}
                        className="admin-select team-select" placeholder="Team…" menuPortalTarget={document.body}
                      />
                    </td>
                    <td>
                      <Select isMulti options={options.roles}
                        value={(user.roles || []).filter(r => r?.id && r?.name).map(r => ({ value: r.id, label: r.name }))}
                        onChange={selected => handleSettingChange(user.id, 'roles', selected)}
                        className={`${user.requested_role_id ? 'select-highlight' : ''} admin-select`} placeholder="Roles…"
                        menuPortalTarget={document.body}
                      />
                    </td>
                    <td>
                      <Select isMulti
                        options={options.donor_groups}
                        value={
                          (user.donor_groups_requested || []).map(dg => ({
                            value: dg,
                            label: `${dg} (Pending)`,
                            isPending: true
                          })).concat(
                            (user.donor_groups || []).filter(dg => !(user.donor_groups_requested || []).includes(dg))
                              .map(dg => ({ value: dg, label: dg }))
                          )
                        }
                        onChange={selected => handleSettingChange(user.id, 'donor_groups', selected)}
                        className={`admin-select ${(user.donor_groups_requested || []).length > 0 ? 'select-highlight' : ''}`}
                        placeholder="Donors…"
                        menuPortalTarget={document.body}
                        styles={{
                          multiValue: (styles, { data }) => ({
                            ...styles,
                            backgroundColor: data.isPending ? '#ffeb3b' : '#e3f2fd'
                          })
                        }}
                      />
                      {(user.donor_groups_requested || []).length > 0 && (
                        <div className="pending-indicator">
                          <i className="fa-solid fa-clock"></i>
                          <span>{(user.donor_groups_requested || []).length} pending</span>
                        </div>
                      )}
                    </td>
                    <td>
                      <Select isMulti
                        options={options.outcomes}
                        value={
                          (user.outcomes_requested || []).map(oid => {
                            const opt = options.outcomes.find(o => o.value === oid)
                            return { ...opt, label: `${opt?.label || oid} (Pending)`, isPending: true }
                          }).concat(
                            (user.outcomes || []).filter(oid => !(user.outcomes_requested || []).includes(oid))
                              .map(oid => {
                                const opt = options.outcomes.find(o => o.value === oid)
                                return opt || { value: oid, label: oid }
                              })
                          )
                        }
                        onChange={selected => handleSettingChange(user.id, 'outcomes', selected)}
                        className={`admin-select ${(user.outcomes_requested || []).length > 0 ? 'select-highlight' : ''}`}
                        placeholder="Outcomes…"
                        menuPortalTarget={document.body}
                        styles={{
                          multiValue: (styles, { data }) => ({
                            ...styles,
                            backgroundColor: data.isPending ? '#ffeb3b' : '#e3f2fd'
                          })
                        }}
                      />
                      {(user.outcomes_requested || []).length > 0 && (
                        <div className="pending-indicator">
                          <i className="fa-solid fa-clock"></i>
                          <span>{(user.outcomes_requested || []).length} pending</span>
                        </div>
                      )}
                    </td>
                    <td>
                      <Select isMulti
                        options={options.field_contexts}
                        value={
                          (user.field_contexts_requested || []).map(fcid => {
                            const opt = options.field_contexts.find(fc => fc.value === fcid)
                            return { ...opt, label: `${opt?.label || fcid} (Pending)`, isPending: true }
                          }).concat(
                            (user.field_contexts || []).filter(fcid => !(user.field_contexts_requested || []).includes(fcid))
                              .map(fcid => {
                                const opt = options.field_contexts.find(fc => fc.value === fcid)
                                return opt || { value: fcid, label: fcid }
                              })
                          )
                        }
                        onChange={selected => handleSettingChange(user.id, 'field_contexts', selected)}
                        className={`admin-select ${(user.field_contexts_requested || []).length > 0 ? 'select-highlight' : ''}`}
                        placeholder="Field Contexts…"
                        menuPortalTarget={document.body}
                        styles={{
                          multiValue: (styles, { data }) => ({
                            ...styles,
                            backgroundColor: data.isPending ? '#ffeb3b' : '#e3f2fd'
                          })
                        }}
                      />
                      {(user.field_contexts_requested || []).length > 0 && (
                        <div className="pending-indicator">
                          <i className="fa-solid fa-clock"></i>
                          <span>{(user.field_contexts_requested || []).length} pending</span>
                        </div>
                      )}
                    </td>
                    <td>
                      <button className="icon-button delete-button" onClick={() => handleDeleteUser(user.id)} title="Delete User">
                        <i className="fa-solid fa-trash-can"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {roleRequests.length > 0 && (
          <div className="admin-section">
            <h3><i className="fa-solid fa-user-shield"></i> Pending Role Requests</h3>
            <div className="users-table-container">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>User</th><th>Requested Role</th><th>Requested</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {roleRequests.map(req => (
                    <tr key={req.user_id} className="row-highlight">
                      <td>
                        <div className="user-info">
                          <span className="user-name">{req.user_name}</span>
                          <span className="user-email">{req.user_email}</span>
                        </div>
                      </td>
                      <td><span className="role-badge">{req.requested_role_name}</span></td>
                      <td>{req.requested_at ? new Date(req.requested_at).toLocaleDateString() : '—'}</td>
                      <td>
                        <button
                          className="primary-button small"
                          onClick={() => {
                            setSelectedRequest(req)
                            setShowRoleRequestModal(true)
                          }}
                          disabled={processingRequest}
                        >
                          <i className="fa-solid fa-check"></i> Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {settingsRequests.length > 0 && (
          <div className="admin-section">
            <h3><i className="fa-solid fa-cog"></i> Pending Settings Requests</h3>
            <div className="users-table-container">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Setting Type</th>
                    <th>Requested Value</th>
                    <th>Requested</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {settingsRequests.map(req => (
                    <tr key={req.request_id} className="row-highlight">
                      <td>
                        <div className="user-info">
                          <span className="user-name">{req.user_name}</span>
                          <span className="user-email">{req.user_email}</span>
                        </div>
                      </td>
                      <td>
                        <span className="setting-type-badge">
                          {req.setting_type.replace('_focal', '').replace('_', ' ')}
                        </span>
                      </td>
                      <td>{req.display_name || req.setting_value}</td>
                      <td>{req.requested_at ? new Date(req.requested_at).toLocaleDateString() : '—'}</td>
                      <td>
                        <button
                          className="primary-button small"
                          onClick={() => {
                            setSelectedRequest(req)
                            setShowSettingsRequestModal(true)
                          }}
                          disabled={processingRequest}
                        >
                          <i className="fa-solid fa-check"></i> Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {options.template_requests.length > 0 && (
          <div className="admin-section">
            <h3><i className="fa-solid fa-file-lines"></i> Donor Template Requests</h3>
            <div className="users-table-container">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>Template Name</th><th>Type</th><th>Requester</th><th>Status</th><th>Download</th>
                  </tr>
                </thead>
                <tbody>
                  {options.template_requests.map(req => (
                    <tr key={req.id} className={req.status === 'pending' ? 'row-highlight' : ''}>
                      <td>
                        <div className="user-info">
                          <span className="user-name">{req.name}</span>
                          <span className="user-email">{req.donor_name || 'Multiple Donors'}</span>
                        </div>
                      </td>
                      <td><span className="template-type-badge">{req.template_type}</span></td>
                      <td>{req.creator_name}</td>
                      <td><span className={`status-badge ${req.status}`}>{req.status}</span></td>
                      <td>
                        <button className="primary-button small" onClick={() => handleDownloadTemplate(req)}>
                          <i className="fa-solid fa-download"></i> JSON
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Role Request Approval Modal */}
      {showRoleRequestModal && selectedRequest && (
        <div className="modal-overlay">
          <div className="modal role-request-modal">
            <button
              className="modal-close"
              onClick={() => {
                setShowRoleRequestModal(false)
                setApprovalNote('')
              }}
            >
              <i className="fa-solid fa-times"></i>
            </button>

            <h3><i className="fa-solid fa-user-shield"></i> Role Request Review</h3>

            <div className="modal-body">
              <div className="request-info">
                <div className="info-row">
                  <strong>User:</strong> {selectedRequest.user_name}
                </div>
                <div className="info-row">
                  <strong>Email:</strong> {selectedRequest.user_email}
                </div>
                <div className="info-row">
                  <strong>Requested Role:</strong> <span className="role-badge">{selectedRequest.requested_role_name}</span>
                </div>
                <div className="info-row">
                  <strong>Requested On:</strong> {selectedRequest.requested_at ? new Date(selectedRequest.requested_at).toLocaleString() : '—'}
                </div>
              </div>

              <div className="admin-note-section">
                <label>Admin Note (optional):</label>
                <textarea
                  value={approvalNote}
                  onChange={e => setApprovalNote(e.target.value)}
                  placeholder="Add a note for audit purposes..."
                  rows={3}
                />
              </div>

              <div className="modal-actions">
                <button
                  className="ghost-button"
                  onClick={handleRejectRoleRequest}
                  disabled={processingRequest}
                >
                  <i className="fa-solid fa-times-circle"></i> Reject Request
                </button>
                <button
                  className="primary-button"
                  onClick={handleApproveRoleRequest}
                  disabled={processingRequest}
                >
                  <i className="fa-solid fa-check-circle"></i> Approve Request
                </button>
              </div>

              {processingRequest && (
                <div className="processing-indicator">
                  <i className="fa-solid fa-spinner fa-spin"></i> Processing...
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
