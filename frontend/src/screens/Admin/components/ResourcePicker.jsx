import React, { useState, useMemo } from 'react'

/**
 * Generic resource picker that shows a searchable table of all resources
 * (proposals/knowledge cards/templates) and lets the admin select one
 * to drill into its access details.
 */
export default function ResourcePicker({ items, loading, error, onSelect, selectedId, columns }) {
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    if (!search.trim()) return items
    const q = search.toLowerCase()
    return items.filter(item =>
      columns.some(col => {
        const val = item[col.key]
        return val && String(val).toLowerCase().includes(q)
      })
    )
  }, [items, search, columns])

  if (loading) {
    return (
      <div className="resource-picker-loading">
        <div className="loading-dots"><span /><span /><span /></div>
        <p>Loading resources…</p>
      </div>
    )
  }

  if (error) {
    return <div className="panel-error">{error}</div>
  }

  if (!items.length) {
    return <div className="resource-picker-empty">No resources found.</div>
  }

  return (
    <div className="resource-picker">
      <div className="resource-picker-search">
        <i className="fa-solid fa-magnifying-glass" />
        <input
          type="text"
          placeholder="Search resources…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <span className="resource-count">{filtered.length} of {items.length}</span>
      </div>
      <div className="resource-picker-table-wrap">
        <table className="resource-picker-table">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col.key}>{col.label}</th>
              ))}
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(item => (
              <tr
                key={item.id}
                className={item.id === selectedId ? 'row-active' : ''}
                onClick={() => onSelect(item.id)}
              >
                {columns.map(col => (
                  <td key={col.key}>
                    {col.render ? col.render(item[col.key], item) : (item[col.key] || '—')}
                  </td>
                ))}
                <td>
                  <button
                    type="button"
                    className={`resource-select-btn ${item.id === selectedId ? 'active' : ''}`}
                    onClick={e => { e.stopPropagation(); onSelect(item.id) }}
                  >
                    {item.id === selectedId ? '● Selected' : 'Manage Access'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
