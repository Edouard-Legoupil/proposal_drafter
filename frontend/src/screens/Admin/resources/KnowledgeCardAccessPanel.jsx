import React, { useMemo, useState } from 'react'
import GrantTable from '../components/GrantTable'
import AuditTimeline from '../components/AuditTimeline'
import SubjectPicker from '../components/SubjectPicker'
import ResourcePicker from '../components/ResourcePicker'
import { useAccessData, useAdminUsers, useAdminOptions, useAdminResourceList } from '../hooks/useAccessData'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

const permissionOptions = [
  { key: 'read', label: 'Read' },
  { key: 'write', label: 'Write' },
  { key: 'patch', label: 'Patch' },
  { key: 'delete', label: 'Delete' }
]

const operationOptions = [
  { value: 'GET', label: 'View (GET)' },
  { value: 'PUT', label: 'Update (PUT)' },
  { value: 'PATCH', label: 'Patch (PATCH)' },
  { value: 'DELETE', label: 'Delete (DELETE)' }
]

const kcColumns = [
  {
    key: 'title', label: 'Knowledge Card',
    render: (val, item) => (
      <div className="user-info">
        <span className="user-name">{(val || 'Untitled').substring(0, 60)}{val?.length > 60 ? '…' : ''}</span>
        <span className="user-email">{item.type || '—'} · {item.donor_name || item.outcome_name || item.field_context_name || '—'}</span>
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

export default function KnowledgeCardAccessPanel({ resourceId: initialResourceId }) {
  const [selectedId, setSelectedId] = useState(initialResourceId !== 'latest' ? initialResourceId : null)
  const [statusMessage, setStatusMessage] = useState('')
  const [grantForm, setGrantForm] = useState({ subjectType: 'user', subjectId: '', permissions: ['read'] })
  const [ownerCandidate, setOwnerCandidate] = useState('')
  const [tester, setTester] = useState({ subjectType: 'user', subjectId: '', operation: 'GET' })
  const [testerResult, setTesterResult] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const { items: cards, loading: listLoading, error: listError } = useAdminResourceList('knowledge-cards')
  const { data: access, loading, error, refresh } = useAccessData(
    selectedId ? `/admin/knowledge-cards/${selectedId}/access` : null
  )
  const { users } = useAdminUsers()
  const { options } = useAdminOptions()

  const ownerLabel = useMemo(() => {
    const owner = access?.knowledge_card?.owner || access?.owner
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

  const handleGrant = async (e) => {
    e.preventDefault()
    if (!grantForm.subjectId) {
      setStatusMessage('Select a subject to grant access')
      return
    }
    setActionLoading(true)
    setStatusMessage('Granting access…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/knowledge-cards/${selectedId}/access`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject_type: grantForm.subjectType,
          subject_id: grantForm.subjectId,
          permissions: grantForm.permissions
        })
      })
      if (!res.ok) throw new Error('Unable to share knowledge card')
      setStatusMessage('Shared successfully')
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
      const res = await fetch(`${API_BASE_URL}/admin/knowledge-cards/${selectedId}/access`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grant_id: grantId })
      })
      if (!res.ok) throw new Error('Failed to revoke access')
      setStatusMessage('Access revoked')
      await refresh()
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleTransfer = async (e) => {
    e.preventDefault()
    if (!ownerCandidate) {
      setStatusMessage('Choose a new owner')
      return
    }
    setActionLoading(true)
    setStatusMessage('Transferring owner…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/knowledge-cards/${selectedId}/owner`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ owner_id: ownerCandidate })
      })
      if (!res.ok) throw new Error('Owner transfer failed')
      setStatusMessage('Owner updated')
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
      setStatusMessage('Select a subject to test')
      return
    }
    setActionLoading(true)
    setStatusMessage('Testing access…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/knowledge-cards/${selectedId}/access/test`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tester)
      })
      if (!res.ok) throw new Error('Tester failed')
      setTesterResult(await res.json())
      setStatusMessage('Tester returned a result')
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
      <section className="knowledge-card-access">
        <header className="section-header">
          <h2>Knowledge Cards — Select a card to manage access</h2>
        </header>
        <ResourcePicker
          items={cards}
          loading={listLoading}
          error={listError}
          onSelect={setSelectedId}
          selectedId={selectedId}
          columns={kcColumns}
        />
      </section>
    )
  }

  if (loading) {
    return (
      <section className="knowledge-card-access">
        <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
          <i className="fa-solid fa-arrow-left" /> All knowledge cards
        </button>
        <div className="panel-loading">Loading knowledge card access…</div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="knowledge-card-access">
        <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
          <i className="fa-solid fa-arrow-left" /> All knowledge cards
        </button>
        <div className="panel-error">{error}</div>
      </section>
    )
  }

  const card = access?.knowledge_card || {}

  return (
    <section className="knowledge-card-access">
      <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
        <i className="fa-solid fa-arrow-left" /> All knowledge cards
      </button>
      <header>
        <h2>{card.title || `Knowledge Card ${selectedId}`}</h2>
        <p><strong>Owner:</strong> {ownerLabel}</p>
        <p>Status: {card.status || '—'}</p>
        {statusMessage && <p className="status-msg">{statusMessage}</p>}
      </header>

      <div className="grant-section">
        <h3>Shared Subjects</h3>
        <GrantTable
          grants={grants}
          permissionOptions={permissionOptions}
          onRevoke={revokeGrant}
          showScope={false}
          emptyMessage="No shared subjects"
        />
        <form className="grant-form" onSubmit={handleGrant}>
          <label>
            Subject type
            <select value={grantForm.subjectType} onChange={e => setGrantForm(prev => ({ ...prev, subjectType: e.target.value, subjectId: '' }))}>
              <option value="user">User</option>
              <option value="team">Team</option>
            </select>
          </label>
          <label>
            {grantForm.subjectType === 'user' ? 'User' : 'Team'}
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
          <button type="submit" className="primary-button" disabled={actionLoading}>Share knowledge card</button>
        </form>
      </div>

      <div className="ownership-panel">
        <h3>Transfer Ownership</h3>
        <form className="ownership-form" onSubmit={handleTransfer}>
          <label>
            New owner
            <SubjectPicker
              subjectType="user"
              value={ownerCandidate}
              onChange={setOwnerCandidate}
              users={users}
              options={options}
              placeholder="Search for new owner…"
            />
          </label>
          <button type="submit" className="primary-button" disabled={actionLoading}>Transfer</button>
        </form>
      </div>

      <div className="tester-panel">
        <h3>Tester</h3>
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
            <p><strong>{testerResult.allowed ? '✅ Allowed' : '❌ Denied'}</strong> — {testerResult.reason || 'No reason provided'}</p>
            <p>Source: {testerResult.source || testerResult.permission_source || '—'}</p>
          </div>
        )}
      </div>

      <section className="audit-panel">
        <div className="section-header">
          <h3>Audit events</h3>
        </div>
        <AuditTimeline events={audit} emptyMessage="No audit events yet" />
      </section>
    </section>
  )
}
