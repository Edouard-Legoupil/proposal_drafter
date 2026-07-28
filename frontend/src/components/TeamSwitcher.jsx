import { useState } from 'react'

import { useAuth } from '../context/AuthContext'

export default function TeamSwitcher() {
  const { activeTeam, memberships, switchTeam } = useAuth()
  const [error, setError] = useState('')
  const activeMemberships = memberships.filter(
    (membership) => !membership.status || membership.status === 'ACTIVE'
  )

  if (activeMemberships.length === 0) return null

  async function handleChange(event) {
    setError('')
    try {
      await switchTeam(event.target.value)
    } catch (switchError) {
      setError(switchError.message)
    }
  }

  return (
    <div>
      <label htmlFor="active-team">Active team</label>
      <select id="active-team" value={activeTeam?.id || ''} onChange={handleChange}>
        {activeMemberships.map((membership) => (
          <option key={membership.id} value={membership.id}>{membership.name}</option>
        ))}
      </select>
      {error && <span role="alert">{error}</span>}
    </div>
  )
}
