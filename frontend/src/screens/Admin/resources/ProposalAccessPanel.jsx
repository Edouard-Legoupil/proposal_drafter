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
  { key: 'delete', label: 'Delete' },
  { key: 'manage', label: 'Manage Access' }
]

const operationOptions = [
  { value: 'GET', label: 'View (GET)' },
  { value: 'PUT', label: 'Update (PUT)' },
  { value: 'PATCH', label: 'Patch (PATCH)' },
  { value: 'DELETE', label: 'Delete (DELETE)' }
]

const proposalColumns = [
  {
    key: 'title', label: 'Proposal',
    render: (val, item) => (
      <div className="user-info">
        <span className="user-name">{val || 'Untitled'}</span>
        <span className="user-email">{item.id?.substring(0, 8)}…</span>
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

export default function ProposalAccessPanel({ resourceId: initialResourceId }) {
  const [selectedId, setSelectedId] = useState(initialResourceId !== 'latest' ? initialResourceId : null)
  const [statusMessage, setStatusMessage] = useState('')
  const [grantForm, setGrantForm] = useState({ subjectType: 'user', subjectId: '', permissions: ['read'], dataScope: 'self' })
  const [ownerCandidate, setOwnerCandidate] = useState('')
  const [tester, setTester] = useState({ subjectType: 'user', subjectId: '', operation: 'GET' })
  const [testerResult, setTesterResult] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const { items: proposals, loading: listLoading, error: listError } = useAdminResourceList('proposals')
  const { data: access, loading, error, refresh } = useAccessData(
    selectedId ? `/admin/proposals/${selectedId}/access` : null
  )
  const { users } = useAdminUsers()
  const { options } = useAdminOptions()

  const ownerLabel = useMemo(() => {
    const owner = access?.proposal?.owner || access?.owner || {}
    if (!owner) return 'Unassigned'
    if (typeof owner === 'string') return owner
    return owner.name || owner.email || owner.id
  }, [access])

  const grants = access?.grants || []
  const audit = access?.audit || []

  const revokeGrant = async (grantId) => {
    setActionLoading(true)
    setStatusMessage('Revoking grant…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/proposals/${selectedId}/access`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grant_id: grantId })
      })
      if (!res.ok) throw new Error('Failed to revoke grant')
      setStatusMessage('Grant revoked')
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
      setStatusMessage('Select a subject before granting access')
      return
    }
    setActionLoading(true)
    setStatusMessage('Saving grant…')
    try {
      const payload = {
        subject_type: grantForm.subjectType,
        subject_id: grantForm.subjectId,
        permissions: grantForm.permissions,
        data_scope: grantForm.dataScope
      }
      const res = await fetch(`${API_BASE_URL}/admin/proposals/${selectedId}/access`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error('Failed to grant access')
      setStatusMessage('Access granted')
      setGrantForm(prev => ({ ...prev, subjectId: '' }))
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
      setStatusMessage('Select a user to become the new owner')
      return
    }
    setActionLoading(true)
    setStatusMessage('Transferring ownership…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/proposals/${selectedId}/owner`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ owner_id: ownerCandidate })
      })
      if (!res.ok) throw new Error('Ownership transfer failed')
      setStatusMessage('Ownership transferred')
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
      setStatusMessage('Select a user/team/donor to test')
      return
    }
    setActionLoading(true)
    setStatusMessage('Running access test…')
    try {
      const res = await fetch(`${API_BASE_URL}/admin/proposals/${selectedId}/access/test`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tester)
      })
      if (!res.ok) throw new Error('Tester failed')
      setTesterResult(await res.json())
      setStatusMessage('Test complete')
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const togglePermission = (key) => {
    setGrantForm(prev => {
      const hasIt = prev.permissions.includes(key)
      const permissions = hasIt
        ? prev.permissions.filter(p => p !== key)
        : [...prev.permissions, key]
      return { ...prev, permissions }
    })
  }

  // Phase 1: Resource picker
  if (!selectedId) {
    return (
      <section className="proposal-access">
        <header className="section-header">
          <h2>Proposals — Select a proposal to manage access</h2>
        </header>
        <ResourcePicker
          items={proposals}
          loading={listLoading}
          error={listError}
          onSelect={setSelectedId}
          selectedId={selectedId}
          columns={proposalColumns}
        />
      </section>
    )
  }

  // Phase 2: Access detail for selected proposal
  if (loading) {
    return (
      <section className="proposal-access">
        <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
          <i className="fa-solid fa-arrow-left" /> All proposals
        </button>
        <div className="panel-loading">Loading proposal access…</div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="proposal-access">
        <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
          <i className="fa-solid fa-arrow-left" /> All proposals
        </button>
        <div className="panel-error">{error}</div>
      </section>
    )
  }

  const proposal = access?.proposal || {}

  return (
    <section className="proposal-access">
      <button type="button" className="ghost-button back-btn" onClick={() => setSelectedId(null)}>
        <i className="fa-solid fa-arrow-left" /> All proposals
      </button>

      <header className="proposal-access-header">
        <div>
          <p className="eyebrow">Proposal</p>
          <h2>{proposal.title || proposal.name || selectedId}</h2>
          <p className="owner"><strong>Owner:</strong> {ownerLabel}</p>
        </div>
        <div className="proposal-meta">
          <p>Status: {proposal.status || '—'}</p>
          <p>Last updated: {proposal.updated_at ? new Date(proposal.updated_at).toLocaleString() : '—'}</p>
          {statusMessage && <p className="status-msg">{statusMessage}</p>}
        </div>
      </header>

      <section className="proposal-grants">
        <div className="section-header">
          <h3>Access Grants</h3>
        </div>
        <GrantTable
          grants={grants}
          permissionOptions={permissionOptions}
          onRevoke={revokeGrant}
          showScope
          emptyMessage="No explicit grants"
        />

        <form className="grant-form" onSubmit={handleGrant}>
          <div className="form-row">
            <label>
              Subject type
              <select value={grantForm.subjectType} onChange={e => setGrantForm(prev => ({ ...prev, subjectType: e.target.value, subjectId: '' }))}>
                <option value="user">User</option>
                <option value="team">Team</option>
                <option value="donor_group">Donor Group</option>
              </select>
            </label>
            <label>
              {grantForm.subjectType === 'user' ? 'User' : grantForm.subjectType === 'team' ? 'Team' : 'Donor Group'}
              <SubjectPicker
                subjectType={grantForm.subjectType}
                value={grantForm.subjectId}
                onChange={val => setGrantForm(prev => ({ ...prev, subjectId: val }))}
                users={users}
                options={options}
              />
            </label>
            <label>
              Data scope
              <select value={grantForm.dataScope} onChange={e => setGrantForm(prev => ({ ...prev, dataScope: e.target.value }))}>
                <option value="self">Self</option>
                <option value="team">Team</option>
                <option value="organization">Organization</option>
                <option value="global">Global</option>
              </select>
            </label>
          </div>
          <div className="form-row permissions-row">
            {permissionOptions.map(opt => (
              <label key={opt.key}>
                <input
                  type="checkbox"
                  checked={grantForm.permissions.includes(opt.key)}
                  onChange={() => togglePermission(opt.key)}
                />
                {opt.label}
              </label>
            ))}
          </div>
          <button type="submit" className="primary-button" disabled={actionLoading}>Save grant</button>
        </form>
      </section>

      <section className="ownership-panel">
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
      </section>

      <section className="tester-panel">
        <h3>Effective Access Tester</h3>
        <form className="tester-form" onSubmit={handleTester}>
          <div className="form-row">
            <label>
              Subject type
              <select value={tester.subjectType} onChange={e => setTester(prev => ({ ...prev, subjectType: e.target.value, subjectId: '' }))}>
                <option value="user">User</option>
                <option value="team">Team</option>
                <option value="donor_group">Donor Group</option>
              </select>
            </label>
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
                {operationOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button type="submit" className="primary-button" disabled={actionLoading}>Run test</button>
        </form>
        {testerResult && (
          <article className="tester-result">
            <p>
              <strong>{testerResult.allowed ? '✅ Allowed' : '❌ Denied'}</strong> — {testerResult.reason || 'No reason provided'}
            </p>
            <p>Source: {testerResult.source || testerResult.permission_source || '—'}</p>
            <p>HTTP status: {testerResult.http_status || testerResult.status || '—'}</p>
            <p>Scope: {testerResult.data_scope || '—'}</p>
          </article>
        )}
      </section>

      <section className="audit-panel">
        <div className="section-header">
          <h3>Recent Audit Events</h3>
        </div>
        <AuditTimeline events={audit.slice(0, 6)} emptyMessage="No recent audit events" />
      </section>
    </section>
  )
}
