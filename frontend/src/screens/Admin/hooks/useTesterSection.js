import { useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

/**
 * Hook to manage tester form state and operations.
 * @param {{ endpoint: string, initialForm: object, refresh?: Function }} params
 */
export function useTesterSection({ endpoint, initialForm, refresh }) {
  const [tester, setTester] = useState(initialForm || { subjectType: 'user', subjectId: '', operation: 'view_dashboard' })
  const [testerResult, setTesterResult] = useState(null)
  const [statusMessage, setStatusMessage] = useState(endpoint ? '' : 'Metrics access testing not available')
  const [actionLoading, setActionLoading] = useState(false)

  const handleTester = async (e) => {
    e.preventDefault()
    if (!endpoint) {
      setStatusMessage('Metrics access testing not available')
      return
    }
    if (!tester.subjectId) {
      setStatusMessage('Select a subject to test')
      return
    }
    setActionLoading(true)
    setStatusMessage('Running access test…')
    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tester)
      })
      if (!res.ok) throw new Error('Tester failed')
      const json = await res.json()
      setTesterResult(json)
      setStatusMessage('Test complete')
      if (refresh) await refresh()
    } catch (err) {
      console.error(err)
      setStatusMessage(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  return { tester, setTester, testerResult, statusMessage, actionLoading, handleTester }
}
