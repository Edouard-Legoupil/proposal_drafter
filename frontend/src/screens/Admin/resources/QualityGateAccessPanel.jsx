import React, { useState } from 'react'
import GrantTable from '../components/GrantTable'
import AuditTimeline from '../components/AuditTimeline'
import SubjectPicker from '../components/SubjectPicker'
import { useAccessData, useAdminUsers, useAdminOptions } from '../hooks/useAccessData'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

const permissionOptions = [
  { key: 'view_page', label: 'View Quality Gate' },
  { key: 'view_queue', label: 'View Incident Queue' },
  { key: 'view_incident', label: 'View Incident' },
  { key: 'create_incident', label: 'Create Incident' },
  { key: 'edit_incident', label: 'Edit Incident' },
  { key: 'assign_incident', label: 'Assign Incident' },
  { key: 'change_status', label: 'Change Status' },
  { key: 'approve', label: 'Approve' },
  { key: 'reject', label: 'Reject' },
  { key: 'export', label: 'Export' },
  { key: 'manage', label: 'Manage Access' }
]

const operationOptions = [
  { value: 'view_quality_gate', label: 'Open page' },
  { value: 'view_incident', label: 'View incident' },
  { value: 'change_status', label: 'Change status' },
  { value: 'export', label: 'Export incidents' }
]

export default function QualityGateAccessPanel({ resourceId }) {
  const [statusMessage, setStatusMessage] = useState('')
  const [grantForm, setGrantForm] = useState({ subjectType: 'user', subjectId: '', permissions: ['view_page'] })
  const [workflow, setWorkflow] = useState({ transition: 'New->Triaged', allowedRoles: '' })
  const [tester, setTester] = useState({ subjectType: 'user', subjectId: '', operation: 'view_quality_gate' })
  const [testerResult, setTesterResult] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const { data: access, loading, error, refresh } = useAccessData(`/admin/quality-gate/access/${resourceId}`)
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
    if (!grantForm.subjectId) { setStatusMessage('Select a subject'); return }
    setActionLoading(true)
    setStatusMessage('Saving grant…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/quality-gate/access/${resourceId}`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(grantForm)
      })
      if (!res.ok) throw new Error('Grant failed')
      setStatusMessage('Grant recorded')
      setGrantForm(prev => ({ ...prev, subjectId: '' }))
      await refresh()
    } catch (err) { setStatusMessage(err.message) }
    finally { setActionLoading(false) }
  }

  const revokeGrant = async (grantId) => {
    setActionLoading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/quality-gate/access/${resourceId}`, {
        method: 'DELETE', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grant_id: grantId })
      })
      if (!res.ok) throw new Error('Unable to revoke')
      await refresh()
    } catch (err) { setStatusMessage(err.message) }
    finally { setActionLoading(false) }
  }

  const handleWorkflowSave = async (e) => {
    e.preventDefault()
    setActionLoading(true)
    setStatusMessage('Saving workflow rule…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/quality-gate/workflow`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflow)
      })
      if (!res.ok) throw new Error('Workflow save failed')
      setStatusMessage('Workflow rule saved')
    } catch (err) { setStatusMessage(err.message) }
    finally { setActionLoading(false) }
  }

  const handleTester = async (e) => {
    e.preventDefault()
    if (!tester.subjectId) { setStatusMessage('Select a subject to test'); return }
    setActionLoading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/admin/quality-gate/access/${resourceId}/test`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tester)
      })
      if (!res.ok) throw new Error('Tester failed')
      setTesterResult(await res.json())
    } catch (err) { setStatusMessage(err.message) }
    finally { setActionLoading(false) }
  }

  if (loading) return <div className="panel-loading">Loading quality gate access…</div>
  if (error) return <div className="panel-error">{error}</div>

  return (
    <section className="quality-gate-access">
      <header>
        <h2>Quality Gate / Incident Access</h2>
        {statusMessage && <p className="status-msg">{statusMessage}</p>}
      </header>
      <section className="grants">
        <div className="section-header"><h3>Grant permissions</h3></div>
        <GrantTable grants={grants} permissionOptions={permissionOptions} onRevoke={revokeGrant} showScope={false} emptyMessage="No incident grants" />
        <form className="grant-form" onSubmit={handleGrant}>
          <label>Subject type
            <select value={grantForm.subjectType} onChange={e => setGrantForm(prev => ({ ...prev, subjectType: e.target.value, subjectId: '' }))}>
              <option value="user">User</option><option value="team">Team</option><option value="role">Role</option>
            </select>
          </label>
          <label>Subject
            <SubjectPicker subjectType={grantForm.subjectType} value={grantForm.subjectId}
              onChange={val => setGrantForm(prev => ({ ...prev, subjectId: val }))} users={users} options={options} />
          </label>
          <fieldset className="permissions-row">
            {permissionOptions.map(opt => (
              <label key={opt.key}><input type="checkbox" checked={grantForm.permissions.includes(opt.key)} onChange={() => togglePermission(opt.key)} />{opt.label}</label>
            ))}
          </fieldset>
          <button type="submit" className="primary-button" disabled={actionLoading}>Grant</button>
        </form>
      </section>
      <section className="workflow">
        <h3>Workflow rule</h3>
        <form className="workflow-form" onSubmit={handleWorkflowSave}>
          <label>Transition
            <input value={workflow.transition} onChange={e => setWorkflow(prev => ({ ...prev, transition: e.target.value }))} />
          </label>
          <label>Allowed roles/users
            <input value={workflow.allowedRoles} onChange={e => setWorkflow(prev => ({ ...prev, allowedRoles: e.target.value }))} />
          </label>
          <button type="submit" className="primary-button" disabled={actionLoading}>Save rule</button>
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
        <div className="section-header"><h3>Audit trail</h3></div>
        <AuditTimeline events={audit} emptyMessage="No workflow events" />
      </section>
    </section>
  )
}
