import { useMemo, useState } from 'react'

const permissions = ['read', 'edit', 'delete']

export default function PermissionsMatrix({ rows = [] }) {
  const [search, setSearch] = useState('')
  const filtered = useMemo(() => rows.filter((row) =>
    `${row.subject} ${row.resource}`.toLowerCase().includes(search.toLowerCase())
  ), [rows, search])

  return (
    <section>
      <label htmlFor="permission-search">Search permissions</label>
      <input id="permission-search" placeholder="Search permissions…" value={search} onChange={(event) => setSearch(event.target.value)} />
      <table>
        <thead><tr><th scope="col">Subject</th><th scope="col">Resource</th>{permissions.map((permission) => <th scope="col" key={permission}>{permission[0].toUpperCase() + permission.slice(1)}</th>)}</tr></thead>
        <tbody>{filtered.map((row) => <tr key={row.id}><th scope="row">{row.subject}</th><td>{row.resource}</td>{permissions.map((permission) => <td key={permission}>{row.permissions.includes(permission) ? 'Granted' : 'Not granted'}</td>)}</tr>)}</tbody>
      </table>
    </section>
  )
}
