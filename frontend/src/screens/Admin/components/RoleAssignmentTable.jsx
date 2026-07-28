import { Button } from '@mui/material'

export default function RoleAssignmentTable({ roles, assignedRoleKeys, onAssign, onRemove }) {
  return (
    <table>
      <thead><tr><th scope="col">Role</th><th scope="col">Component</th><th scope="col">Assignment</th></tr></thead>
      <tbody>
        {roles.filter((role) => role.component).map((role) => {
          const assigned = assignedRoleKeys.includes(role.role_key)
          return (
            <tr key={role.role_key}>
              <td>{role.name}</td><td>{role.component}</td>
              <td><Button onClick={() => assigned ? onRemove(role.role_key) : onAssign(role.role_key)}>{assigned ? `Remove ${role.name}` : `Assign ${role.name}`}</Button></td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
