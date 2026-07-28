import { useEffect, useMemo, useState } from 'react'
import { Alert, CircularProgress } from '@mui/material'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

export default function UserAccessPanel() {
  const [users, setUsers] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    fetch(`${API_BASE_URL}/admin/users`, { credentials: 'include' })
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load users')
        return response.json()
      })
      .then((data) => { if (active) setUsers(data || []) })
      .catch((loadError) => { if (active) setError(loadError.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const filtered = useMemo(() => users.filter((user) =>
    `${user.name || ''} ${user.email || ''}`.toLowerCase().includes(search.toLowerCase())
  ), [search, users])

  return <section>
    <header><h2>User Access</h2><p>Manage membership and roles from Teams. Direct user-role assignments are not supported.</p></header>
    <label htmlFor="user-search">Search users</label>
    <input id="user-search" placeholder="Search users…" value={search} onChange={(event) => setSearch(event.target.value)} />
    {loading && <CircularProgress aria-label="Loading users" />}
    {error && <Alert severity="error">{error}</Alert>}
    <table><thead><tr><th scope="col">User</th><th scope="col">Email</th><th scope="col">Team memberships</th></tr></thead><tbody>{filtered.map((user) => <tr key={user.id}><th scope="row">{user.name || 'Unnamed user'}</th><td>{user.email}</td><td>{(user.memberships || []).length ? user.memberships.map((membership) => `${membership.name} (${membership.status || 'ACTIVE'})`).join(', ') : 'No active memberships'}</td></tr>)}</tbody></table>
  </section>
}
