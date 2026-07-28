import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { server } from '../../../mocks/server'
import SettingsAccessPanel from './SettingsAccessPanel'

describe('SettingsAccessPanel', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/admin/users', () => HttpResponse.json([{ id: 'user-1', name: 'Amina', email: 'a@example.com' }])),
      http.get('/api/teams', () => HttpResponse.json({ teams: [{ id: 'team-1', name: 'Shelter' }] })),
      http.get('/api/roles', () => HttpResponse.json({ roles: [{ role_key: 'access_template', name: 'Template access', component: 'TemplateWorkspace' }] })),
      http.get('/api/settings', () => HttpResponse.json({ settings: [{ id: 1, user_id: 'user-1', team_id: 'team-1', role_key: 'access_template', key: 'donor', value: 'ECHO' }] }))
    )
  })

  it('displays settings with all three scopes', async () => {
    render(<SettingsAccessPanel />)
    expect((await screen.findAllByText('Amina')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('Shelter').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Template access').length).toBeGreaterThan(0)
    expect(screen.getByText('donor')).toBeInTheDocument()
  })

  it('submits user team and role scoped values', async () => {
    const user = userEvent.setup()
    let payload
    server.use(http.post('/api/settings', async ({ request }) => {
      payload = await request.json()
      return HttpResponse.json({ id: 2, ...payload }, { status: 201 })
    }))
    render(<SettingsAccessPanel />)
    await screen.findAllByText('Amina')
    await user.selectOptions(screen.getByLabelText('User'), 'user-1')
    await user.selectOptions(screen.getByLabelText('Team'), 'team-1')
    await user.selectOptions(screen.getByLabelText('Role'), 'access_template')
    await user.type(screen.getByLabelText('Setting key'), 'country')
    await user.type(screen.getByLabelText('Setting value'), 'Kenya')
    await user.click(screen.getByRole('button', { name: /save setting/i }))
    await waitFor(() => expect(payload).toEqual({ user_id: 'user-1', team_id: 'team-1', role_key: 'access_template', key: 'country', value: 'Kenya' }))
  })
})
