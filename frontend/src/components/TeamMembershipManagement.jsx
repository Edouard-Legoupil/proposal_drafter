import { useCallback, useEffect, useState } from 'react'
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material'

import { useTeamMembership } from '../hooks/useTeamMembership'
import RoleAssignmentTable from '../screens/Admin/components/RoleAssignmentTable'

export function TeamMembershipManagement({ team }) {
  const {
    error,
    getMembers,
    getAvailableUsers,
    addMember,
    getPendingRequests,
    approveMembership,
    rejectMembership,
    removeMember,
    assignLeader,
    removeLeader,
    getAvailableRoles,
    getTeamRoles,
    assignRoleToTeam,
    removeRoleFromTeam,
    canApproveMembership,
    canManageTeamRoles
  } = useTeamMembership()
  const [members, setMembers] = useState([])
  const [availableUsers, setAvailableUsers] = useState([])
  const [newMemberId, setNewMemberId] = useState('')
  const [requests, setRequests] = useState([])
  const [roles, setRoles] = useState([])
  const [assignedRoles, setAssignedRoles] = useState([])
  const [refreshing, setRefreshing] = useState(false)

  const refresh = useCallback(async () => {
    if (!team?.id) return
    setRefreshing(true)
    try {
      const memberPromise = getMembers?.(team.id) || Promise.resolve([])
      const requestPromise = canApproveMembership(team.id) ? getPendingRequests(team.id) : Promise.resolve([])
      const rolePromise = canManageTeamRoles(team.id) ? getTeamRoles(team.id) : Promise.resolve([])
      const availablePromise = canManageTeamRoles(team.id) ? getAvailableRoles() : Promise.resolve([])
      const usersPromise = canManageTeamRoles(team.id) ? getAvailableUsers() : Promise.resolve([])
      const [nextMembers, nextRequests, nextAssigned, nextRoles, nextUsers] = await Promise.all([memberPromise, requestPromise, rolePromise, availablePromise, usersPromise])
      setMembers(nextMembers)
      setRequests(nextRequests)
      setAssignedRoles(nextAssigned)
      setRoles(nextRoles)
      setAvailableUsers(nextUsers.filter((candidate) => !nextMembers.some((member) => member.user_id === candidate.id)))
    } finally {
      setRefreshing(false)
    }
  }, [canApproveMembership, canManageTeamRoles, getAvailableRoles, getAvailableUsers, getMembers, getPendingRequests, getTeamRoles, team?.id])

  useEffect(() => { refresh() }, [refresh])
  if (!team) return <Alert severity="info">No team selected</Alert>

  async function act(operation) { if (await operation()) await refresh() }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5">{team.name} Management</Typography>
      {error && <Alert severity="error">{error}</Alert>}
      {refreshing && <CircularProgress aria-label="Refreshing team" />}
      <Typography variant="h6">Members</Typography>
      {canManageTeamRoles(team.id) && <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <label htmlFor="team-user-to-add">User to add</label>
        <select id="team-user-to-add" value={newMemberId} onChange={(event) => setNewMemberId(event.target.value)}>
          <option value="">Select user</option>
          {availableUsers.map((candidate) => <option key={candidate.id} value={candidate.id}>{candidate.name} ({candidate.email})</option>)}
        </select>
        <Button disabled={!newMemberId} onClick={() => act(async () => {
          const added = await addMember(team.id, newMemberId)
          if (added) setNewMemberId('')
          return added
        })}>Add member</Button>
      </Box>}
      <ul>{members.map((member) => <li key={member.user_id}>
        {member.name} ({member.email}) {member.is_leader && <strong>TEAM_LEADER</strong>}
        <Button aria-label={`${member.is_leader ? 'Remove' : 'Make'} ${member.name} team leader`} onClick={() => act(() => member.is_leader ? removeLeader(team.id, member.user_id) : assignLeader(team.id, member.user_id))}>{member.is_leader ? 'Remove leader' : 'Make leader'}</Button>
        <Button onClick={() => act(() => removeMember(team.id, member.user_id))}>Remove member</Button>
      </li>)}</ul>
      {canApproveMembership(team.id) && <><Typography variant="h6">Pending Membership Requests</Typography><ul>{requests.map((request) => <li key={request.user_id}>{request.user_name} ({request.user_email}) <Button onClick={() => act(() => approveMembership(team.id, request.user_id))}>Approve</Button><Button onClick={() => act(() => rejectMembership(team.id, request.user_id))}>Reject</Button></li>)}</ul></>}
      {canManageTeamRoles(team.id) && <>
        <Typography variant="h6">Component Roles</Typography>
        <p>TEAM_LEADER is assigned per member, not to the whole team.</p>
        <RoleAssignmentTable roles={roles} assignedRoleKeys={assignedRoles.map((role) => role.role_key)} onAssign={(roleKey) => act(() => assignRoleToTeam(team.id, roleKey))} onRemove={(roleKey) => act(() => removeRoleFromTeam(team.id, roleKey))} />
      </>}
    </Box>
  )
}
