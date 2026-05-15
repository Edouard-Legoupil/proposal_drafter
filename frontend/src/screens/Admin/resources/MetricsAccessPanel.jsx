import React, { useState } from 'react'
import GrantTable from '../components/GrantTable'
import AuditTimeline from '../components/AuditTimeline'
import SubjectPicker from '../components/SubjectPicker'
import { useAccessData, useAdminUsers, useAdminOptions } from '../hooks/useAccessData'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

const metricPermissions = [
  { key: 'view_dashboard', label: 'View Dashboard' },
  { key: 'export_metrics', label: 'Export Metrics' },
  { key: 'configure_dashboard', label: 'Configure Dashboard' },
  { key: 'manage_metrics', label: 'Manage Metrics Access' }
]

const operationOptions = [
  { value: 'view_dashboard', label: 'Open Dashboard' },
  { value: 'view_widget', label: 'View Widget' },
  { value: 'export', label: 'Export Metrics' }
]

const dataScopes = ['self', 'team', 'organization', 'global']

export default function MetricsAccessPanel({ resourceId }) {
  const [statusMessage, setStatusMessage] = useState('')
  const [grantForm, setGrantForm] = useState({ subjectType: 'user', subjectId: '', permissions: ['view_dashboard'], dataScope: 'self' })
  const [tester, setTester] = useState({ subjectType: 'user', subjectId: '', operation: 'view_dashboard' })
  const [testerResult, setTesterResult] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const { data: access, loading, error, refresh } = useAccessData(`/admin/metrics/access/${resourceId}`)
  const { users } = useAdminUsers()
  const { options } = useAdminOptions()

  const grants = access?.grants || []
  const audit = access?.audit || []

  const togglePermission = (key) => {
    setGrantForm(prev => {
      const hasIt = prev.permissions.includes(key)
      const permissions = hasIt ? prev.permissions.filter(p => p !== key) : [...prev.permissions, key]
      return { ...prev, permissions }
    })
  }

  const handleGrant = async (e) => {
    e.preventDefault()
    if (!grantForm.subjectId) { setStatusMessage('Select a subject first'); return }
    setActionLoading(true)
    setStatusMessage('Saving metrics grant…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/metrics/access/${resourceId}`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(grantForm)
      })
      if (!res.ok) throw new Error('Unable to grant metrics access')
      setStatusMessage('Grant saved')
      setGrantForm(prev => ({ ...prev, subjectId: '' }))
      await refresh()
    } catch (err) { setStatusMessage(err.message) }
    finally { setActionLoading(false) }
  }

  const revokeGrant = async (grantId) => {
    setActionLoading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/metrics/access/${resourceId}`, {
        method: 'DELETE', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grant_id: grantId })
      })
      if (!res.ok) throw new Error('Unable to revoke')
      await refresh()
    } catch (err) { setStatusMessage(err.message) }
    finally { setActionLoading(false) }
  }

  const handleTester = async (e) => {
    e.preventDefault()
    if (!tester.subjectId) { setStatusMessage('Select a subject to test'); return }
    setActionLoading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/metrics/access/${resourceId}/test`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tester)
      })
      if (!res.ok) throw new Error('Tester failed')
      setTesterResult(await res.json())
    } catch (err) { setStatusMessage(err.message) }
    finally { setActionLoading(false) }
  }

  if (loading) return <div className="panel-loading">Loading metrics access…</div>
  if (error) return <div className="panel-error">{error}</div>

  return (
    <section className="metrics-access">
      <header>
        <h2>Metrics Dashboard</h2>
        {statusMessage && <p className="status-msg">{statusMessage}</p>}
      </header>
      <section className="grants-table">
        <div className="section-header"><h3>Grants</h3></div>
        <GrantTable grants={grants} permissionOptions={metricPermissions} onRevoke={revokeGrant} showScope emptyMessage="No dashboard grants" />
        <form className="grant-form" onSubmit={handleGrant}>
          <label>Subject type
            <select value={grantForm.subjectType} onChange={e => setGrantForm(prev => ({ ...prev, subjectType: e.target.value, subjectId: '' }))}>
              <option value="user">User</option><option value="team">Team</option><option value="donor_group">Donor Group</option>
            </select>
          </label>
          <label>Subject
            <SubjectPicker subjectType={grantForm.subjectType} value={grantForm.subjectId}
              onChange={val => setGrantForm(prev => ({ ...prev, subjectId: val }))} users={users} options={options} />
          </label>
          <label>Data scope
            <select value={grantForm.dataScope} onChange={e => setGrantForm(prev => ({ ...prev, dataScope: e.target.value }))}>
              {dataScopes.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <fieldset className="permissions-row">
            {metricPermissions.map(opt => (
              <label key={opt.key}><input type="checkbox" checked={grantForm.permissions.includes(opt.key)} onChange={() => togglePermission(opt.key)} />{opt.label}</label>
            ))}
          </fieldset>
          <button type="submit" className="primary-button" disabled={actionLoading}>Grant</button>
        </form>
      </section>
      <section className="tester">
        <h3>Tester</h3>
        <form className="tester-form" onSubmit={handleTester}>
          <label>Subject
            <SubjectPicker subjectType={tester.subjectType} value={tester.subjectId}
              onChange={val => setTester(prev => ({ ...prev, subjectId: val }))} users={users} options={options} />
          </label>
          <label>Operation
            <select value={tester.operation} onChange={e => setTester(prev => ({ ...prev, operation: e.target.value }))}>
              {operationOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </label>
          <button type="submit" className="primary-button" disabled={actionLoading}>Test</button>
        </form>
        {testerResult && (
          <div className="tester-result">
            <p><strong>{testerResult.allowed ? '✅ Allowed' : '❌ Denied'}</strong> — {testerResult.reason || '—'}</p>
          </div>
        )}
      </section>
      <section className="audit-panel">
        <div className="section-header"><h3>Audit</h3></div>
        <AuditTimeline events={audit} emptyMessage="No audit events" />
      </section>
    </section>
  )
}
