import { describe, expect, it } from 'vitest'

import {
  canManageTeamRoles,
  hasObjectAccess,
  hasPermission,
  isTeamLeaderOf,
  isTeamMember
} from './roleUtils'

describe('active-team role utilities', () => {
  const user = {
    id: 'user-1',
    is_admin: false,
    active_team: { id: 'team-a', name: 'Alpha' },
    memberships: [{ id: 'team-a', name: 'Alpha' }],
    roles: ['access_template'],
    team_leadership: true
  }

  it('checks only active-team roles', () => {
    expect(hasPermission(user, 'access_template')).toBe(true)
    expect(hasPermission({ ...user, roles: [], all_roles: ['access_template'] }, 'access_template')).toBe(false)
  })

  it('scopes membership and leadership to the active team', () => {
    expect(isTeamMember(user, 'team-a')).toBe(true)
    expect(isTeamMember(user, 'team-b')).toBe(false)
    expect(isTeamLeaderOf(user, 'team-a')).toBe(true)
    expect(isTeamLeaderOf(user, 'team-b')).toBe(false)
  })

  it('does not grant object access from ownership or membership defaults', () => {
    expect(hasObjectAccess(user, { owner_id: 'user-1', team_id: 'team-a' }, 'read')).toBe(false)
    expect(hasObjectAccess(user, { team_id: 'team-a', access_rules: [] }, 'read')).toBe(false)
  })

  it('reserves component-role management for system administrators', () => {
    expect(canManageTeamRoles(user, 'team-a')).toBe(false)
    expect(canManageTeamRoles({ ...user, is_admin: true }, 'team-a')).toBe(true)
  })
})
