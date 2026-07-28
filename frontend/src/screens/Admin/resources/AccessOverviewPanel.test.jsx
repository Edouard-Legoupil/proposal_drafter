import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import AccessOverviewPanel from './AccessOverviewPanel'

describe('AccessOverviewPanel', () => {
  afterEach(() => vi.restoreAllMocks())

  it('builds the matrix from team roles and real object grants', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url) => {
      const path = String(url)
      let payload = []
      if (path.endsWith('/teams')) payload = { teams: [{ id: 'team-1', name: 'Shelter team' }] }
      else if (path.endsWith('/teams/team-1/roles')) payload = { roles: [{ role_key: 'proposal writer', component: 'ProposalWorkspace' }] }
      else if (path.endsWith('/admin/proposals/list')) payload = [{ id: 'proposal-1', title: 'Shelter plan' }]
      else if (path.endsWith('/admin/knowledge-cards/list') || path.endsWith('/admin/templates/list')) payload = []
      else if (path.endsWith('/admin/proposals/proposal-1/access')) payload = {
        grants: [{ id: 'grant-1', subject_type: 'team', subject_id: 'team-1', permissions: ['read', 'edit'] }]
      }
      return { ok: true, json: async () => payload }
    })

    render(<AccessOverviewPanel />)

    expect(await screen.findByText(/Component: ProposalWorkspace.*proposal writer/i)).toBeInTheDocument()
    expect(await screen.findByText('Proposal: Shelter plan')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Access' })).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalledWith(expect.stringContaining('/settings'), expect.anything())
  })
})
