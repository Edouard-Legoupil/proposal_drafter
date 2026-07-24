import React, { useMemo, useState } from 'react'
import ResourcePicker from '../components/ResourcePicker'
import AuditTimeline from '../components/AuditTimeline'
import GrantSection from '../components/GrantSection'
import TesterSection from '../components/TesterSection'
import ErrorBanner from '../components/ErrorBanner'
import SubjectPicker from '../components/SubjectPicker'
import { useAccessData, useAdminUsers, useAdminOptions, useAdminResourceList } from '../hooks/useAccessData'
import { useGrantSection } from '../hooks/useGrantSection'
import { useTesterSection } from '../hooks/useTesterSection'

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
  const [ownerCandidate, setOwnerCandidate] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const { items: proposals, loading: listLoading, error: listError } = useAdminResourceList('proposals')
  const { data: access, loading, error, refresh } = useAccessData(
    selectedId ? `/admin/proposals/${selectedId}/access` : null
  )
  const { grantForm, setGrantForm, statusMessage: grantMsg, actionLoading: grantLoading, handleGrant, revokeGrant } =
    useGrantSection({
      endpoint: `/admin/proposals/${selectedId}/access`,
      initialForm: { subjectType: 'user', subjectId: '', permissions: ['read'], dataScope: 'self' },
      refresh
    })
  const { tester, setTester, testerResult, statusMessage: testMsg, actionLoading: testLoading, handleTester } =
    useTesterSection({
      endpoint: `/admin/proposals/${selectedId}/access/test`,
      initialForm: { subjectType: 'user', subjectId: '', operation: 'GET' }
    })

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
        <ErrorBanner message={error} />
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
        <GrantSection
          grants={grants}
          permissionOptions={permissionOptions}
          showScope
          dataScopeOptions={['self','team','organization','global']}
          grantForm={grantForm}
          setGrantForm={setGrantForm}
          statusMessage={grantMsg}
          actionLoading={grantLoading}
          onGrant={handleGrant}
          onRevoke={revokeGrant}
          users={users}
          options={options}
          emptyMessage="No explicit grants"
        />

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
        <TesterSection
          tester={tester}
          setTester={setTester}
          testerResult={testerResult}
          statusMessage={testMsg}
          actionLoading={testLoading}
          onTest={handleTester}
          operationOptions={operationOptions}
          users={users}
          options={options}
        />
      </section>

      <section className="audit-panel">
        <div className="section-header">
          <h3>Audit Timeline</h3>
        </div>
        <AuditTimeline events={audit.slice(0, 6)} emptyMessage="No recent audit events" />
      </section>
    </section>
  )
}
