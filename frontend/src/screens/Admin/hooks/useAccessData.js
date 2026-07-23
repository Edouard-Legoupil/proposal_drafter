import { useState, useCallback, useEffect } from 'react'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

export function useAccessData(relativePath) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(!!relativePath)
  const [error, setError] = useState(relativePath ? '' : 'Metrics access management not available')

  const fetchData = useCallback(async () => {
    if (!relativePath) {
      setError('Metrics access management not available')
      setLoading(false)
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE_URL}${relativePath}`, {
        credentials: 'include'
      })
      if (!res.ok) {
        const errorMsg = `Failed to load access data (${res.status})`
        // Special handling for 404 errors
        if (res.status === 404) {
          setError('Metrics access management not available')
        } else {
          setError(errorMsg)
        }
        return
      }
      const payload = await res.json()
      setData(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [relativePath])

  useEffect(() => {
    if (relativePath) {
      fetchData()
    } else {
      setData(null)
      setLoading(false)
      setError('')
    }
  }, [fetchData, relativePath])

  return { data, loading, error, refresh: fetchData }
}

export function useAdminUsers() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    async function load() {
      setLoading(true)
      try {
        const res = await fetch(`${API_BASE_URL}/admin/users`, {
          credentials: 'include',
          signal: controller.signal
        })
        if (!res.ok) {
          throw new Error('Unable to load users')
        }
        if (active) {
          setUsers(await res.json())
        }
      } catch (err) {
        if (active) setError(err.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => {
      active = false
      controller.abort()
    }
  }, [])

  return { users, loading, error }
}

export function useAdminOptions() {
  const [options, setOptions] = useState({
    roles: [],
    donor_groups: [],
    outcomes: [],
    field_contexts: [],
    teams: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      try {
        const res = await fetch(`${API_BASE_URL}/admin/options`, {
          credentials: 'include'
        })
        if (!res.ok) throw new Error('Unable to load options')
        const data = await res.json()
        if (active) {
          setOptions({
            roles: (data.roles || []).map(r => ({ value: r.id, label: r.name })),
            donor_groups: (data.donor_groups || []).map(dg => ({ value: dg, label: dg })),
            outcomes: (data.outcomes || []).map(o => ({ value: o.id, label: o.name })),
            field_contexts: (data.field_contexts || []).map(fc => ({ value: fc.id, label: fc.name })),
            teams: (data.teams || []).map(t => ({ value: t.id, label: t.name }))
          })
        }
      } catch (err) {
        if (active) setError(err.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [])

  return { options, loading, error }
}

export function useAdminResourceList(resourceType) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        // Special handling for incidents which use a different endpoint
        const endpoint = resourceType === 'incidents'
          ? `${API_BASE_URL}/incidents/admin/list`
          : `${API_BASE_URL}/admin/${resourceType}/list`

        const res = await fetch(endpoint, {
          credentials: 'include'
        })
        if (!res.ok) throw new Error(`Failed to load ${resourceType} list (${res.status})`)
        if (active) setItems(await res.json())
      } catch (err) {
        if (active) setError(err.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    if (resourceType) load()
    return () => { active = false }
  }, [resourceType])

  return { items, loading, error }
}
