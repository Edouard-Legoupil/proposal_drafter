import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from 'react'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'
const AuthContext = createContext(undefined)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    async function loadProfile() {
      try {
        const response = await fetch(`${API_BASE_URL}/profile`, {
          credentials: 'include'
        })

        if (!response.ok) {
          return
        }

        const data = await response.json()
        if (active) {
          setUser(data.user || null)
        }
      } catch {
        if (active) {
          setUser(null)
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadProfile()
    return () => {
      active = false
    }
  }, [])

  const updateUser = useCallback((nextUser) => {
    setUser(nextUser)
  }, [])

  const value = useMemo(
    () => ({ user, loading, updateUser }),
    [user, loading, updateUser]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
