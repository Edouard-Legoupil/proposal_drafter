import React, { useMemo, useState } from 'react'
import GrantSection from '../components/GrantSection'
import AuditTimeline from '../components/AuditTimeline'
import ErrorBanner from '../components/ErrorBanner'
import SubjectPicker from '../components/SubjectPicker'
import ResourcePicker from '../components/ResourcePicker'
import { useAccessData, useAdminUsers, useAdminOptions, useAdminResourceList } from '../hooks/useAccessData'
import { useGrantSection } from '../hooks/useGrantSection'
import { useTesterSection } from '../hooks/useTesterSection'
import TesterSection from '../components/TesterSection'

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
  const [ownerCandidate, setOwnerCandidate] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const { items: cards, loading: listLoading, error: listError } = useAdminResourceList('knowledge-cards')
  const { data: access, loading, error, refresh } = useAccessData(
    selectedId ? `/admin/knowledge-cards/${selectedId}/access` : null
  )
  const { grantForm, setGrantForm, statusMessage: grantMsg, actionLoading: grantLoading, handleGrant, revokeGrant } =
    useGrantSection({
      endpoint: `/admin/knowledge-cards/${selectedId}/access`,
      initialForm: { subjectType: 'user', subjectId: '', permissions: ['read'] },
      refresh
    })
  const { tester, setTester, testerResult, statusMessage: testMsg, actionLoading: testLoading, handleTester } =
    useTesterSection({
      endpoint: `/admin/knowledge-cards/${selectedId}/access/test`,
      initialForm: { subjectType: 'user', subjectId: '', operation: 'GET' }
    })

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
        <ErrorBanner message={error} />
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
        <GrantSection
          grants={grants}
          permissionOptions={permissionOptions}
          showScope={false}
          grantForm={grantForm}
          setGrantForm={setGrantForm}
          statusMessage={grantMsg}
          actionLoading={grantLoading}
          onGrant={handleGrant}
          onRevoke={revokeGrant}
          users={users}
          options={options}
          emptyMessage="No shared subjects"
        />
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
          subjectTypeOptions={['user', 'team']}
        />
      </div>

      <section className="audit-panel">
        <div className="section-header">
          <h3>Audit Timeline</h3>
        </div>
        <AuditTimeline events={audit} emptyMessage="No audit events yet" />
      </section>
    </section>
  )
}
