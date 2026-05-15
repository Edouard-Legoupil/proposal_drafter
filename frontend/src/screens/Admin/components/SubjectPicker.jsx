import React, { useMemo } from 'react'
import Select from 'react-select'

/**
 * Searchable subject picker that populates options based on subject type.
 * Replaces raw text inputs for user/team/donor_group/role/organization selection.
 */
export default function SubjectPicker({
  subjectType,
  value,
  onChange,
  users = [],
  options = {},
  placeholder,
  className = 'admin-select',
  isClearable = true
}) {
  const selectOptions = useMemo(() => {
    switch (subjectType) {
      case 'user':
        return users.map(u => ({
          value: u.id,
          label: `${u.name || 'Unnamed'} (${u.email})`,
          email: u.email,
          name: u.name
        }))
      case 'team':
        return (options.teams || []).map(t => ({
          value: typeof t === 'object' ? (t.value || t.id) : t,
          label: typeof t === 'object' ? (t.label || t.name) : t
        }))
      case 'donor_group':
        return (options.donor_groups || []).map(dg => ({
          value: typeof dg === 'object' ? (dg.value || dg) : dg,
          label: typeof dg === 'object' ? (dg.label || dg) : dg
        }))
      case 'role':
        return (options.roles || []).map(r => ({
          value: typeof r === 'object' ? (r.value || r.id) : r,
          label: typeof r === 'object' ? (r.label || r.name) : r
        }))
      case 'organization':
        return [{ value: 'organization', label: 'Organization' }]
      default:
        return []
    }
  }, [subjectType, users, options])

  const selectedValue = useMemo(() => {
    if (!value) return null
    return selectOptions.find(o => String(o.value) === String(value)) || { value, label: value }
  }, [value, selectOptions])

  const defaultPlaceholder = {
    user: 'Search users by name or email…',
    team: 'Select a team…',
    donor_group: 'Select a donor group…',
    role: 'Select a role…',
    organization: 'Select organization…'
  }

  return (
    <Select
      options={selectOptions}
      value={selectedValue}
      onChange={opt => onChange(opt ? String(opt.value) : '')}
      placeholder={placeholder || defaultPlaceholder[subjectType] || 'Select…'}
      className={className}
      classNamePrefix="react-select"
      isClearable={isClearable}
      menuPortalTarget={document.body}
      noOptionsMessage={() =>
        subjectType === 'user'
          ? 'No users found'
          : `No ${subjectType?.replace('_', ' ')}s available`
      }
      styles={{
        menuPortal: base => ({ ...base, zIndex: 9999 }),
        control: base => ({ ...base, minHeight: 38 }),
        option: (base, state) => ({
          ...base,
          fontSize: '0.875rem',
          background: state.isFocused ? '#e8f0fe' : 'white',
          color: '#1e293b'
        })
      }}
    />
  )
}
