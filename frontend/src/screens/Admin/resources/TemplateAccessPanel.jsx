import React, { useMemo, useState } from 'react'
import GrantTable from '../components/GrantTable'
import AuditTimeline from '../components/AuditTimeline'
import SubjectPicker from '../components/SubjectPicker'
import ResourcePicker from '../components/ResourcePicker'
import { useAccessData, useAdminUsers, useAdminOptions, useAdminResourceList } from '../hooks/useAccessData'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

const visibilityModes = [
  { value: 'private', label: 'Private' },
  { value: 'organization', label: 'Public to organization' },
  { value: 'restricted', label: 'Restricted to subjects' }
]

const permissionOptions = [
  { key: 'read', label: 'Read/Use' },
  { key: 'edit', label: 'Edit' },
  { key: 'delete', label: 'Delete' },
  { key: 'manage', label: 'Manage Access' }
]

const operationOptions = [
  { value: 'view', label: 'View/Use' },
  { value: 'edit', label: 'Edit' },
  { value: 'delete', label: 'Delete' },
  { value: 'share', label: 'Share/Manage Access' }
]

const templateColumns = [
  {
    key: 'name', label: 'Template',
    render: (val, item) => (
      <div className="user-info">
        <span className="user-name">{val || 'Untitled'}</span>
        <span className="user-email">{item.template_type || '—'}{item.is_default ? ' · Default' : ''}</span>
      </div>
    )
  },
  {
    key: 'status', label: 'Status',
    render: val => <span className={`status-badge ${val || 'draft'}`}>{val || 'draft'}</span>
  },
  { key: 'owner_name', label: 'Owner' },
  {
    key: 'updated_at', label: 'Last Updated',
    render: val => val ? new Date(val).toLocaleDateString() : '—'
  }
]

export default function TemplateAccessPanel({ resourceId: initialResourceId }) {
  const [selectedId, setSelectedId] = useState(initialResourceId !== 'latest' ? initialResourceId : null)
  const [statusMessage, setStatusMessage] = useState('')
  const [visibility, setVisibility] = useState('private')
  const [grantForm, setGrantForm] = useState({ subjectType: 'user', subjectId: '', permissions: ['read'] })
  const [tester, setTester] = useState({ subjectType: 'user', subjectId: '', operation: 'view' })
  const [testerResult, setTesterResult] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const { items: templates, loading: listLoading, error: listError } = useAdminResourceList('templates')
  const { data: access, loading, error, refresh } = useAccessData(
    selectedId ? `/admin/templates/${selectedId}/access` : null
  )
  const { users } = useAdminUsers()
  const { options } = useAdminOptions()

  const ownerLabel = useMemo(() => {
    const owner = access?.template?.owner || access?.owner
    if (!owner) return 'Unassigned'
    if (typeof owner === 'string') return owner
    return owner.name || owner.email || owner.id
  }, [access])

  const grants = access?.grants || []
  const audit = access?.audit || []

  const togglePermission = (key) => {
    setGrantForm(prev => {
      const hasIt = prev.permissions.includes(key)
      const permissions = hasIt
        ? prev.permissions.filter(p => p !== key)
        : [...prev.permissions, key]
      return { ...prev, permissions }
    })
  }

  const handleVisibilityChange = async (value) => {
    setVisibility(value)
    setActionLoading(true)
    setStatusMessage('Updating visibility…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/templates/${selectedId}/visibility`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ visibility: value })
      })
      if (!res.ok) throw new Error('Unable to update visibility')
      setStatusMessage('Visibility updated')
      await refresh()
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleGrant = async (e) => {
    e.preventDefault()
    if (!grantForm.subjectId) {
      setStatusMessage('Select a subject')
      return
    }
    setActionLoading(true)
    setStatusMessage('Saving grant…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/templates/${selectedId}/access`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject_type: grantForm.subjectType,
          subject_id: grantForm.subjectId,
          permissions: grantForm.permissions
        })
      })
      if (!res.ok) throw new Error('Grant failed')
      setStatusMessage('Grant saved')
      setGrantForm(prev => ({ ...prev, subjectId: '' }))
      await refresh()
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const revokeGrant = async (grantId) => {
    setActionLoading(true)
    setStatusMessage('Revoking…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/templates/${selectedId}/access`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grant_id: grantId })
      })
      if (!res.ok) throw new Error('Unable to revoke grant')
      setStatusMessage('Grant revoked')
      await refresh()
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleTester = async (e) => {
    e.preventDefault()
    if (!tester.subjectId) {
      setStatusMessage('Select a subject for testing')
      return
    }
    setActionLoading(true)
    setStatusMessage('Running template tester…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/templates/${selectedId}/access/test`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tester)
      })
      if (!res.ok) throw new Error('Tester failed')
      setTesterResult(await res.json())
      setStatusMessage('Tester result ready')
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  // Phase 1: Resource picker
  if (!selectedId) {
    return (
      <section className="template-access">
        <header className="section-header">
          <h2>Templates — Select a template to manage access</h2>
        </header>
        <ResourcePicker
          items={templates}
          loading={listLoading}
          error={listError}
          onSelect={setSelectedId}
          selectedId={selectedId}
          columns={templateColumns}
        />
      </section>
    )
  }

  if (loading) {
    return (
      <section className="template-access">
        <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
          <i className="fa-solid fa-arrow-left" /> All templates
        </button>
        <div className="panel-loading">Loading template access…</div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="template-access">
        <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
          <i className="fa-solid fa-arrow-left" /> All templates
        </button>
        <div className="panel-error">{error}</div>
      </section>
    )
  }

  const template = access?.template || {}

  return (
    <section className="template-access">
      <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
        <i className="fa-solid fa-arrow-left" /> All templates
      </button>
      <header>
        <h2>{template.title || `Template ${selectedId}`}</h2>
        <p><strong>Owner:</strong> {ownerLabel}</p>
        <p>Visibility: {template.visibility || visibility}</p>
        {statusMessage && <p className="status-msg">{statusMessage}</p>}
      </header>

      <div className="visibility-row">
        <label>
          Visibility mode
          <select value={visibility} onChange={e => handleVisibilityChange(e.target.value)}>
            {visibilityModes.map(mode => (
              <option key={mode.value} value={mode.value}>{mode.label}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="grant-section">
        <h3>Granted subjects</h3>
        <GrantTable
          grants={grants}
          permissionOptions={permissionOptions}
          onRevoke={revokeGrant}
          showScope
          emptyMessage="No template grants"
        />
        <form className="grant-form" onSubmit={handleGrant}>
          <label>
            Subject type
            <select value={grantForm.subjectType} onChange={e => setGrantForm(prev => ({ ...prev, subjectType: e.target.value, subjectId: '' }))}>
              <option value="user">User</option>
              <option value="team">Team</option>
              <option value="organization">Organization</option>
            </select>
          </label>
          <label>
            {grantForm.subjectType === 'user' ? 'User' : grantForm.subjectType === 'team' ? 'Team' : 'Organization'}
            <SubjectPicker
              subjectType={grantForm.subjectType}
              value={grantForm.subjectId}
              onChange={val => setGrantForm(prev => ({ ...prev, subjectId: val }))}
              users={users}
              options={options}
            />
          </label>
          <fieldset className="permissions-row">
            {permissionOptions.map(opt => (
              <label key={opt.key}>
                <input type="checkbox" checked={grantForm.permissions.includes(opt.key)} onChange={() => togglePermission(opt.key)} />
                {opt.label}
              </label>
            ))}
          </fieldset>
          <button type="submit" className="primary-button" disabled={actionLoading}>Save grant</button>
        </form>
      </div>

      <section className="tester-panel">
        <div className="section-header">
          <h3>Tester</h3>
        </div>
        <form className="tester-form" onSubmit={handleTester}>
          <label>
            Subject
            <SubjectPicker
              subjectType={tester.subjectType}
              value={tester.subjectId}
              onChange={val => setTester(prev => ({ ...prev, subjectId: val }))}
              users={users}
              options={options}
            />
          </label>
          <label>
            Operation
            <select value={tester.operation} onChange={e => setTester(prev => ({ ...prev, operation: e.target.value }))}>
              {operationOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </label>
          <button type="submit" className="primary-button" disabled={actionLoading}>Test</button>
        </form>
        {testerResult && (
          <div className="tester-result">
            <p><strong>{testerResult.allowed ? '✅ Allowed' : '❌ Denied'}</strong> — {testerResult.reason || 'No reason'}</p>
          </div>
        )}
      </section>

      <section className="audit-panel">
        <div className="section-header">
          <h3>Audit</h3>
        </div>
        <AuditTimeline events={audit} emptyMessage="No audit yet" />
      </section>
    </section>
  )
}
