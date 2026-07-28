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

  const applyAccessContext = useCallback((profileUser, accessContext = profileUser) => {
    const memberships = (accessContext?.memberships || profileUser?.memberships || [])
      .filter((membership) => !membership.status || membership.status === 'ACTIVE')
    const roles = accessContext?.roles || accessContext?.role_keys || []
    const nextUser = profileUser
      ? {
          ...profileUser,
          memberships,
          active_team: accessContext?.active_team || null,
          roles,
          role_keys: accessContext?.role_keys || roles,
          team_leadership: Boolean(accessContext?.team_leadership),
          settings: accessContext?.settings || {}
        }
      : null
    setUser(nextUser)
  }, [])

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
          applyAccessContext(data.user || null)
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
  }, [applyAccessContext])

  const updateUser = useCallback((nextUser) => {
    applyAccessContext(nextUser)
  }, [applyAccessContext])

  const switchTeam = useCallback(async (teamId) => {
    const response = await fetch(`${API_BASE_URL}/profile/active-team`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id: teamId })
    })
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.detail || 'Unable to switch team')
    }
    const context = await response.json()
    setUser((currentUser) => {
      if (!currentUser) return currentUser
      const memberships = (context.memberships || currentUser.memberships || [])
        .filter((membership) => !membership.status || membership.status === 'ACTIVE')
      const roles = context.roles || context.role_keys || []
      return {
        ...currentUser,
        memberships,
        active_team: context.active_team,
        roles,
        role_keys: context.role_keys || roles,
        team_leadership: Boolean(context.team_leadership),
        settings: context.settings || {}
      }
    })
    return context
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      updateUser,
      activeTeam: user?.active_team || null,
      memberships: user?.memberships || [],
      roles: user?.roles || [],
      settings: user?.settings || {},
      switchTeam
    }),
    [user, loading, updateUser, switchTeam]
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
