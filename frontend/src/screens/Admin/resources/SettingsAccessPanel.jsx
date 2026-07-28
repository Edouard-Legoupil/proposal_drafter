import { useCallback, useEffect, useState } from 'react'
import { Alert, Button, TextField, Typography } from '@mui/material'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

async function request(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...options })
  const data = response.status === 204 ? null : await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data?.detail || 'Request failed')
  return data
}

export default function SettingsAccessPanel() {
  const [users, setUsers] = useState([])
  const [teams, setTeams] = useState([])
  const [roles, setRoles] = useState([])
  const [settings, setSettings] = useState([])
  const [form, setForm] = useState({ user_id: '', team_id: '', role_key: '', key: '', value: '' })
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [userData, teamData, roleData, settingData] = await Promise.all([
        request('/admin/users'), request('/teams'), request('/roles'), request('/settings')
      ])
      setUsers(userData || [])
      setTeams(teamData.teams || [])
      setRoles((roleData.roles || []).filter((role) => role.component))
      setSettings(settingData.settings || [])
    } catch (loadError) { setError(loadError.message) }
  }, [])
  useEffect(() => { load() }, [load])

  const names = (items, id, key = 'id') => items.find((item) => String(item[key]) === String(id))?.name || id
  async function submit(event) {
    event.preventDefault()
    setError('')
    try {
      await request('/settings', { method: 'POST', body: JSON.stringify(form) })
      await load()
      setForm((current) => ({ ...current, key: '', value: '' }))
    } catch (submitError) { setError(submitError.message) }
  }
  async function remove(id) { await request(`/settings/${id}`, { method: 'DELETE' }); await load() }

  return <section>
    <Typography variant="h2">Scoped Settings</Typography>
    <p>Settings apply only after user membership and the selected team role are authorized.</p>
    {error && <Alert severity="error">{error}</Alert>}
    <form onSubmit={submit}>
      <label>User<select aria-label="User" value={form.user_id} onChange={(event) => setForm({ ...form, user_id: event.target.value })}><option value="">Select user</option>{users.map((user) => <option key={user.id} value={user.id}>{user.name || user.email}</option>)}</select></label>
      <label>Team<select aria-label="Team" value={form.team_id} onChange={(event) => setForm({ ...form, team_id: event.target.value })}><option value="">Select team</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>
      <label>Role<select aria-label="Role" value={form.role_key} onChange={(event) => setForm({ ...form, role_key: event.target.value })}><option value="">Select role</option>{roles.map((role) => <option key={role.role_key} value={role.role_key}>{role.name}</option>)}</select></label>
      <TextField label="Setting key" value={form.key} onChange={(event) => setForm({ ...form, key: event.target.value })} />
      <TextField label="Setting value" value={form.value} onChange={(event) => setForm({ ...form, value: event.target.value })} />
      <Button type="submit" disabled={Object.values(form).some((value) => !value)}>Save setting</Button>
    </form>
    <table><thead><tr><th>User</th><th>Team</th><th>Role</th><th>Key</th><th>Value</th><th>Action</th></tr></thead><tbody>{settings.map((setting) => <tr key={setting.id}><td>{names(users, setting.user_id)}</td><td>{names(teams, setting.team_id)}</td><td>{names(roles, setting.role_key, 'role_key')}</td><td>{setting.key}</td><td>{String(setting.value)}</td><td><Button onClick={() => remove(setting.id)}>Delete</Button></td></tr>)}</tbody></table>
  </section>
}
