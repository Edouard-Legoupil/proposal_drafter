import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import './AdminAccess.css'
import UserAccessPanel from './resources/UserAccessPanel'
import ProposalAccessPanel from './resources/ProposalAccessPanel'
import KnowledgeCardAccessPanel from './resources/KnowledgeCardAccessPanel'
import TemplateAccessPanel from './resources/TemplateAccessPanel'
import TeamsAccessPanel from './resources/TeamsAccessPanel'
import Base from '../../components/Base/Base'

const resourcePanels = {
  'user-access': UserAccessPanel,
  teams: TeamsAccessPanel,
  proposals: ProposalAccessPanel,
  'knowledge-cards': KnowledgeCardAccessPanel,
  templates: TemplateAccessPanel
}

const navItems = [
  { key: 'user-access', label: 'User Access' },
  { key: 'teams', label: 'Teams' },
  { key: 'proposals', label: 'Proposals' },
  { key: 'knowledge-cards', label: 'Knowledge Cards' },
  { key: 'templates', label: 'Templates' }
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
    <Base>
      <div className="admin-access-shell">
        <header>
          <h1>Access Management</h1>
          <p className="admin-access-subtitle">
            Manage user access, team roles, and object-level permissions for proposals, knowledge cards, and templates.
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
    </Base>
  )
}
