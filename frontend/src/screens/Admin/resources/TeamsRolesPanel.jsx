import React, { useState, useEffect } from 'react'
import Select from 'react-select'
import '../TeamsRolesPanel.css'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "/api"

export default function TeamsRolesPanel() {
  const [teams, setTeams] = useState([])
  const [roles, setRoles] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTeam, setSelectedTeam] = useState(null)
  const [selectedRole, setSelectedRole] = useState(null)
  const [selectedUsers, setSelectedUsers] = useState([])
  const [newTeamName, setNewTeamName] = useState('')
  const [newRoleName, setNewRoleName] = useState('')
  const [bulkOperation, setBulkOperation] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const [teamsRes, rolesRes, usersRes] = await Promise.all([
          fetch(`${API_BASE_URL}/admin/options`, { credentials: 'include' }),
          fetch(`${API_BASE_URL}/admin/options`, { credentials: 'include' }),
          fetch(`${API_BASE_URL}/admin/users`, { credentials: 'include' })
        ])

        if (teamsRes.ok && rolesRes.ok && usersRes.ok) {
          const teamsData = await teamsRes.json()
          const usersData = await usersRes.json()
          
          setTeams(teamsData.teams || [])
          setRoles(teamsData.roles || [])
          setUsers(usersData || [])
        } else {
          setError("Failed to fetch teams and roles data")
        }
      } catch (err) {
        console.error(err)
        setError("An error occurred while fetching data")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return
    
    try {
      const response = await fetch(`${API_BASE_URL}/admin/teams`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newTeamName }),
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setTeams(prev => [...prev, data.team])
        setNewTeamName('')
      } else {
        const errorData = await response.json()
        alert(errorData.detail || "Failed to create team.")
      }
    } catch (err) {
      alert("Error creating team.")
    }
  }

  const handleCreateRole = async () => {
    if (!newRoleName.trim()) return
    
    try {
      const response = await fetch(`${API_BASE_URL}/admin/roles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newRoleName }),
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setRoles(prev => [...prev, data.role])
        setNewRoleName('')
      } else {
        const errorData = await response.json()
        alert(errorData.detail || "Failed to create role.")
      }
    } catch (err) {
      alert("Error creating role.")
    }
  }

  const handleBulkAssign = async () => {
    if (!bulkOperation || selectedUsers.length === 0) return
    
    try {
      const updates = selectedUsers.map(userId => {
        if (bulkOperation === 'team' && selectedTeam) {
          return fetch(`${API_BASE_URL}/admin/users/${userId}/team`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team_id: selectedTeam.value }),
            credentials: 'include'
          })
        } else if (bulkOperation === 'role' && selectedRole) {
          // For roles, we need to get the user's current settings and add the new role
          return fetch(`${API_BASE_URL}/admin/users/${userId}/settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              role_ids: [selectedRole.value],
              donor_groups: [],
              outcomes: [],
              field_contexts: []
            }),
            credentials: 'include'
          })
        }
        return Promise.resolve()
      })

      await Promise.all(updates)
      alert(`Successfully assigned ${bulkOperation} to ${selectedUsers.length} users`)
      setSelectedUsers([])
      setBulkOperation('')
    } catch (err) {
      alert('Some bulk operations failed.')
    }
  }

  const toggleUserSelection = (userId) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    )
  }

  const filteredUsers = users.filter(user => 
    (user.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (user.email?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  )

  return (
    <div className="teams-roles-panel">
      <header className="section-header">
        <h2>Teams & Roles Management</h2>
      </header>

      {/* Summary stats */}
      <div className="admin-stats-row">
        <div className="admin-stat-card">
          <span className="stat-value">{teams.length}</span>
          <span className="stat-label">Total Teams</span>
        </div>
        <div className="admin-stat-card">
          <span className="stat-value">{roles.length}</span>
          <span className="stat-label">Total Roles</span>
        </div>
        <div className="admin-stat-card">
          <span className="stat-value">{users.length}</span>
          <span className="stat-label">Total Users</span>
        </div>
      </div>

      {/* Create new team/role */}
      <div className="admin-section">
        <h3>Create New</h3>
        <div className="create-forms">
          <div className="create-team-form">
            <input
              type="text"
              placeholder="New Team Name"
              value={newTeamName}
              onChange={e => setNewTeamName(e.target.value)}
              className="create-input"
            />
            <button className="primary-button small" onClick={handleCreateTeam} disabled={!newTeamName.trim()}>
              <i className="fa-solid fa-plus"></i> Create Team
            </button>
          </div>
          <div className="create-role-form">
            <input
              type="text"
              placeholder="New Role Name"
              value={newRoleName}
              onChange={e => setNewRoleName(e.target.value)}
              className="create-input"
            />
            <button className="primary-button small" onClick={handleCreateRole} disabled={!newRoleName.trim()}>
              <i className="fa-solid fa-plus"></i> Create Role
            </button>
          </div>
        </div>
      </div>

      {/* Bulk assignment */}
      <div className="admin-section">
        <h3>Bulk Assignment</h3>
        <div className="bulk-assignment-controls">
          <select
            value={bulkOperation}
            onChange={e => setBulkOperation(e.target.value)}
            className="admin-select"
          >
            <option value="">Select operation…</option>
            <option value="team">Assign Team</option>
            <option value="role">Assign Role</option>
          </select>

          {bulkOperation === 'team' && (
            <Select
              options={teams.map(t => ({ value: t.id, label: t.name }))}
              value={selectedTeam}
              onChange={setSelectedTeam}
              placeholder="Select team…"
              className="admin-select"
              menuPortalTarget={document.body}
            />
          )}

          {bulkOperation === 'role' && (
            <Select
              options={roles.map(r => ({ value: r.id, label: r.name }))}
              value={selectedRole}
              onChange={setSelectedRole}
              placeholder="Select role…"
              className="admin-select"
              menuPortalTarget={document.body}
            />
          )}

          <button
            className="primary-button small"
            onClick={handleBulkAssign}
            disabled={!bulkOperation || (!selectedTeam && !selectedRole) || selectedUsers.length === 0}
          >
            Assign to Selected Users
          </button>
        </div>

        {/* User search and selection */}
        <div className="user-search">
          <input
            type="text"
            placeholder="Search users…"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <span className="user-count">{filteredUsers.length} users found</span>
        </div>

        {selectedUsers.length > 0 && (
          <div className="selection-info">
            <strong>{selectedUsers.length}</strong> users selected
            <button className="ghost-button small" onClick={() => setSelectedUsers([])}>
              Clear Selection
            </button>
          </div>
        )}

        {/* User table */}
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th style={{ width: 40 }}>
                  <input
                    type="checkbox"
                    checked={selectedUsers.length === filteredUsers.length && filteredUsers.length > 0}
                    onChange={() => setSelectedUsers(
                      selectedUsers.length === filteredUsers.length 
                        ? [] 
                        : filteredUsers.map(u => u.id)
                    )}
                  />
                </th>
                <th>User</th>
                <th>Current Team</th>
                <th>Current Roles</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map(user => (
                <tr key={user.id} className={selectedUsers.includes(user.id) ? 'row-selected' : ''}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedUsers.includes(user.id)}
                      onChange={() => toggleUserSelection(user.id)}
                    />
                  </td>
                  <td>
                    <div className="user-info">
                      <span className="user-name">{user.name}</span>
                      <span className="user-email">{user.email}</span>
                    </div>
                  </td>
                  <td>{user.team_name || 'No Team'}</td>
                  <td>
                    {user.roles?.length ? (
                      <div className="role-badges">
                        {user.roles.map(role => (
                          <span key={role.id} className="role-badge">
                            {role.name}
                          </span>
                        ))}
                      </div>
                    ) : 'No Roles'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Teams and Roles lists */}
      <div className="admin-section">
        <div className="lists-container">
          <div className="team-list">
            <h3><i className="fa-solid fa-users"></i> Teams</h3>
            {teams.length === 0 ? (
              <p className="empty-list">No teams found</p>
            ) : (
              <ul className="item-list">
                {teams.map(team => (
                  <li key={team.id} className="item-card">
                    <span className="item-name">{team.name}</span>
                    <span className="item-meta">Team</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="role-list">
            <h3><i className="fa-solid fa-tag"></i> Roles</h3>
            {roles.length === 0 ? (
              <p className="empty-list">No roles found</p>
            ) : (
              <ul className="item-list">
                {roles.map(role => (
                  <li key={role.id} className="item-card">
                    <span className="item-name">{role.name}</span>
                    <span className="item-meta">Role</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}