import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import './AdminAccess.css'
import UserAccessPanel from './resources/UserAccessPanel'
import ProposalAccessPanel from './resources/ProposalAccessPanel'
import KnowledgeCardAccessPanel from './resources/KnowledgeCardAccessPanel'
import TemplateAccessPanel from './resources/TemplateAccessPanel'
import MetricsAccessPanel from './resources/MetricsAccessPanel'
import QualityGateAccessPanel from './resources/QualityGateAccessPanel'

const resourcePanels = {
  users: UserAccessPanel,
  proposals: ProposalAccessPanel,
  'knowledge-cards': KnowledgeCardAccessPanel,
  templates: TemplateAccessPanel,
  metrics: MetricsAccessPanel,
  'quality-gate': QualityGateAccessPanel
}

const navItems = [
  { key: 'users', label: 'Users' },
  { key: 'proposals', label: 'Proposals' },
  { key: 'knowledge-cards', label: 'Knowledge Cards' },
  { key: 'templates', label: 'Templates' },
  { key: 'metrics', label: 'Metrics Dashboard' },
  { key: 'quality-gate', label: 'Quality Gate' }
]

export default function AccessManagement() {
  const { resourceType, resourceId } = useParams()
  const navigate = useNavigate()
  const Panel = resourcePanels[resourceType]

  const navigateTo = (type) => {
    const idSegment = resourceId || 'latest'
    navigate(`/admin/access/${type}/${idSegment}`)
  }

  return (
    <div className="admin-access-shell">
      <header>
        <h1>Access Management</h1>
        <p className="admin-access-subtitle">
          Manage object-level permissions for proposals, knowledge cards, templates, dashboards, and quality gate/incident workflows.
        </p>
      </header>
      <nav className="admin-access-tabs">
        {navItems.map(item => (
          <button
            type="button"
            key={item.key}
            className={item.key === resourceType ? 'active' : ''}
            onClick={() => navigateTo(item.key)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <main className="admin-access-panel">
        {Panel ? (
          <Panel resourceId={resourceId} />
        ) : (
          <section className="admin-access-placeholder">
            <h2>{resourceType ? `Coming soon: ${resourceType}` : 'Select a resource type'}</h2>
            <p>
              We are rolling out the resource-specific access editors starting with proposals. Select a resource from the tabs above to begin.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}
