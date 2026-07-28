import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Box, Button, CircularProgress, List, ListItem, TextField, Typography } from '@mui/material'

import { TeamMembershipManagement } from '../../../components/TeamMembershipManagement'
import { useAuth } from '../../../context/AuthContext'
import TeamForm from '../components/TeamForm'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  const data = response.status === 204 ? null : await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data?.detail
    throw new Error(typeof detail === 'object' ? detail.message : detail || 'Request failed')
  }
  return data
}

export default function TeamsAccessPanel() {
  const { user } = useAuth()
  const [teams, setTeams] = useState([])
  const [selectedTeam, setSelectedTeam] = useState(null)
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadTeams = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await request('/teams')
      setTeams(data.teams || [])
    } catch (loadError) {
      setError(loadError.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadTeams() }, [loadTeams])

  const filteredTeams = useMemo(() => teams.filter((team) =>
    `${team.name} ${team.description || ''}`.toLowerCase().includes(search.toLowerCase())
  ), [search, teams])

  async function saveTeam(values) {
    const data = await request(selectedTeam ? `/teams/${selectedTeam.id}` : '/teams', {
      method: selectedTeam ? 'PATCH' : 'POST',
      body: JSON.stringify(values)
    })
    setTeams((current) => selectedTeam
      ? current.map((team) => team.id === data.id ? data : team)
      : [...current, data])
    setSelectedTeam(data)
    setEditing(false)
  }

  async function deleteTeam() {
    setError('')
    try {
      await request(`/teams/${selectedTeam.id}`, { method: 'DELETE' })
      setTeams((current) => current.filter((team) => team.id !== selectedTeam.id))
      setSelectedTeam(null)
    } catch (deleteError) {
      setError(deleteError.message)
    }
  }

  if (!user?.is_admin) return <Alert severity="error">Admin access required to manage teams.</Alert>

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4">Team Management</Typography>
      {error && <Alert severity="error" sx={{ my: 2 }}>{error}</Alert>}
      {editing ? (
        <TeamForm team={selectedTeam} onSubmit={saveTeam} onCancel={() => setEditing(false)} />
      ) : selectedTeam ? (
        <Box>
          <Button onClick={() => setSelectedTeam(null)}>Back to teams</Button>
          <Button onClick={() => setEditing(true)}>Edit team</Button>
          <Button color="error" onClick={deleteTeam}>Delete team</Button>
          <TeamMembershipManagement team={selectedTeam} />
        </Box>
      ) : (
        <>
          <Box sx={{ display: 'flex', gap: 2, my: 2 }}>
            <TextField placeholder="Search teams…" value={search} onChange={(event) => setSearch(event.target.value)} />
            <Button variant="contained" onClick={() => setEditing(true)}>Create Team</Button>
          </Box>
          {loading ? <CircularProgress aria-label="Loading teams" /> : (
            <List>
              {filteredTeams.map((team) => (
                <ListItem key={team.id}>
                  <Button aria-label={`Manage ${team.name}`} onClick={() => setSelectedTeam(team)}>{team.name}</Button>
                  <span>{team.description}</span>
                </ListItem>
              ))}
            </List>
          )}
        </>
      )}
    </Box>
  )
}
