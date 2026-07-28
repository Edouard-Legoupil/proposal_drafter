import { useEffect, useState } from 'react'

import PermissionsMatrix from '../components/PermissionsMatrix'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

const resourceTypes = [
  { key: 'proposals', label: 'Proposal' },
  { key: 'knowledge-cards', label: 'Knowledge card' },
  { key: 'templates', label: 'Template' }
]

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, { credentials: 'include' })
  if (!response.ok) throw new Error(`Failed to load ${path}`)
  return response.json()
}

function resourceItems(payload, key) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.[key] || []
}

export default function AccessOverviewPanel() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true

    async function loadOverview() {
      try {
        const teamData = await fetchJson('/teams')
        const teams = teamData.teams || []
        const teamNames = Object.fromEntries(teams.map((team) => [team.id, team.name]))
        const rolePayloads = await Promise.all(teams.map((team) => fetchJson(`/teams/${team.id}/roles`)))
        const roleRows = rolePayloads.flatMap((payload, index) =>
          (payload.roles || []).map((role) => ({
            id: `role-${teams[index].id}-${role.role_key}`,
            subject: teams[index].name,
            resource: `Component: ${role.component} (${role.role_key})`,
            permissions: ['access']
          }))
        )

        const resourcePayloads = await Promise.all(
          resourceTypes.map(({ key }) => fetchJson(`/admin/${key}/list`))
        )
        const grantRows = (await Promise.all(resourceTypes.flatMap(({ key, label }, typeIndex) =>
          resourceItems(resourcePayloads[typeIndex], key).map(async (resource) => {
            const access = await fetchJson(`/admin/${key}/${resource.id}/access`)
            return (access.grants || [])
              .filter((grant) => grant.subject_type === 'team')
              .map((grant) => ({
                id: `grant-${grant.id}`,
                subject: teamNames[grant.subject_id] || grant.subject_id,
                resource: `${label}: ${resource.title || resource.name || resource.id}`,
                permissions: grant.permissions || []
              }))
          })
        ))).flat()

        if (active) setRows([...roleRows, ...grantRows])
      } catch (loadError) {
        if (active) setError(loadError.message)
      }
    }

    loadOverview()
    return () => { active = false }
  }, [])
  return <section><h2>Permissions Overview</h2><p>Effective access is team membership + active-team role + explicit team grant.</p>{error ? <p role="alert">{error}</p> : <PermissionsMatrix rows={rows} />}</section>
}
