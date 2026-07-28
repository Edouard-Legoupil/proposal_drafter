import { useEffect, useState } from 'react'

import PermissionsMatrix from '../components/PermissionsMatrix'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

export default function AccessOverviewPanel() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    Promise.all([
      fetch(`${API_BASE_URL}/settings`, { credentials: 'include' }).then((response) => response.json()),
      fetch(`${API_BASE_URL}/teams`, { credentials: 'include' }).then((response) => response.json())
    ]).then(([settingData, teamData]) => {
      if (!active) return
      const teamNames = Object.fromEntries((teamData.teams || []).map((team) => [team.id, team.name]))
      setRows((settingData.settings || []).map((setting) => ({
        id: `setting-${setting.id}`,
        subject: teamNames[setting.team_id] || setting.team_id,
        resource: `${setting.role_key}: ${setting.key}`,
        permissions: ['read', 'edit']
      })))
    }).catch((loadError) => setError(loadError.message))
    return () => { active = false }
  }, [])
  return <section><h2>Permissions Overview</h2><p>Effective access is team membership + active-team role + explicit team grant.</p>{error ? <p role="alert">{error}</p> : <PermissionsMatrix rows={rows} />}</section>
}
