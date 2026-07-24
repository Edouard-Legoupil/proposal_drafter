import { useEffect, useState } from 'react'
import Select from 'react-select'
import './UserSettingsModal.css'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

const EMPTY_PREFERENCES = {
  geographic_coverage_type: null,
  geographic_coverage_region: null,
  geographic_coverage_country: null
}

export default function UserSettingsModal({ show, onClose }) {
  const [teamOptions, setTeamOptions] = useState([])
  const [selectedTeams, setSelectedTeams] = useState([])
  const [approvedTeamIds, setApprovedTeamIds] = useState([])
  const [pendingTeamIds, setPendingTeamIds] = useState([])
  const [preferences, setPreferences] = useState(EMPTY_PREFERENCES)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!show) return undefined

    const controller = new AbortController()
    async function fetchInitialData() {
      setLoading(true)
      setError('')
      try {
        const requestOptions = { credentials: 'include', signal: controller.signal }
        const [settingsResponse, teamsResponse, pendingResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/users/me/settings`, requestOptions),
          fetch(`${API_BASE_URL}/teams`, requestOptions),
          fetch(`${API_BASE_URL}/settings/requests/pending`, requestOptions)
        ])

        if (!settingsResponse.ok || !teamsResponse.ok || !pendingResponse.ok) {
          throw new Error('Unable to load your access settings')
        }

        const [settings, teamsPayload, pendingPayload] = await Promise.all([
          settingsResponse.json(),
          teamsResponse.json(),
          pendingResponse.json()
        ])
        const options = (teamsPayload.teams || []).map(team => ({
          value: String(team.id),
          label: team.name
        }))
        const approvedIds = (settings.team_memberships || []).map(String)
        const requestedIds = (settings.requested_team_memberships || []).map(String)
        const pendingIds = (pendingPayload.pending_requests || [])
          .filter(request => request.setting_type === 'team_membership')
          .map(request => String(request.setting_value))
        const allPendingIds = [...new Set([...requestedIds, ...pendingIds])]
        const selectedIds = new Set([...approvedIds, ...allPendingIds])

        setTeamOptions(options)
        setApprovedTeamIds(approvedIds)
        setPendingTeamIds(allPendingIds)
        setSelectedTeams(options.filter(option => selectedIds.has(option.value)))
        setPreferences({
          geographic_coverage_type: settings.geographic_coverage_type ?? null,
          geographic_coverage_region: settings.geographic_coverage_region ?? null,
          geographic_coverage_country: settings.geographic_coverage_country ?? null
        })
      } catch (fetchError) {
        if (fetchError.name !== 'AbortError') setError(fetchError.message)
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    fetchInitialData()
    return () => controller.abort()
  }, [show])

  const handleTeamChange = (nextTeams = []) => {
    const lockedIds = new Set([...approvedTeamIds, ...pendingTeamIds])
    const nextIds = new Set(nextTeams.map(team => team.value))
    const lockedTeams = teamOptions.filter(team => lockedIds.has(team.value) && !nextIds.has(team.value))
    setSelectedTeams([...nextTeams, ...lockedTeams])
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    const approvedIds = new Set(approvedTeamIds)
    const requestedTeamIds = selectedTeams
      .map(team => team.value)
      .filter(teamId => !approvedIds.has(teamId))

    try {
      const response = await fetch(`${API_BASE_URL}/users/me/settings`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...preferences,
          requested_team_memberships: requestedTeamIds
        })
      })
      if (!response.ok) throw new Error('Unable to save your access settings')
      onClose()
    } catch (saveError) {
      setError(saveError.message)
    } finally {
      setSaving(false)
    }
  }

  const teamStyles = {
    multiValue: (styles, { data }) => ({
      ...styles,
      backgroundColor: pendingTeamIds.includes(data.value) ? '#ff9800' : styles.backgroundColor
    }),
    multiValueLabel: (styles, { data }) => ({
      ...styles,
      color: pendingTeamIds.includes(data.value) ? 'white' : styles.color
    }),
    multiValueRemove: (styles, { data }) => ({
      ...styles,
      display: approvedTeamIds.includes(data.value) || pendingTeamIds.includes(data.value) ? 'none' : styles.display
    })
  }

  if (!show) return null

  return (
    <div className="user-settings-overlay" onClick={onClose}>
      <div className="user-settings-modal" role="dialog" aria-modal="true" aria-labelledby="settings-title" onClick={event => event.stopPropagation()}>
        <div className="modal-header">
          <h2 id="settings-title">Access and Permissions Management</h2>
          <button type="button" className="close-x" aria-label="Close settings" onClick={onClose}>&times;</button>
        </div>

        {loading ? (
          <div className="modal-loading">Loading settings...</div>
        ) : (
          <form onSubmit={handleSubmit} className="modal-form">
            <div className="modal-instructions">
              <p>Request membership in teams whose access you need. Existing memberships cannot be changed here.</p>
              <p className="approval-note">⏱ New requests require team-leader approval and appear in orange until processed.</p>
            </div>

            {error && <p className="status-msg" role="alert">{error}</p>}

            <div className="form-section">
              <label htmlFor="user-settings-teams">Team Membership</label>
              <Select
                inputId="user-settings-teams"
                isMulti
                options={teamOptions}
                value={selectedTeams}
                onChange={handleTeamChange}
                className="settings-select"
                styles={teamStyles}
                placeholder="Select teams to join..."
              />
              <p className="field-hint">Orange items are pending team-leader approval.</p>
            </div>

            <div className="modal-footer">
              <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
              <button type="submit" className="save-btn" disabled={saving}>
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
