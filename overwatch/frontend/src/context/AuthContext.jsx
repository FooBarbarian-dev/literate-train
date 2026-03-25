import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import client, { setCsrfToken, clearCsrfToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const verify = useCallback(async () => {
    try {
      const response = await client.get('/accounts/verify/')
      setUser(response.data)
      return true
    } catch {
      // Stale session — drop any cached CSRF token so the next login
      // starts with a clean slate.
      clearCsrfToken()
      setUser(null)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    verify()
  }, [verify])

  const login = async (username, password) => {
    const response = await client.post('/accounts/login/', { username, password })
    // Store the fresh CSRF token issued by the server on login so it can be
    // sent as X-CSRF-Token on subsequent mutating requests.
    if (response.data.csrfToken) {
      setCsrfToken(response.data.csrfToken)
    }
    setUser(response.data.user || response.data)
    return response.data
  }

  const logout = async () => {
    try {
      await client.post('/accounts/logout/')
    } catch {
      // ignore logout errors
    }
    // Clear the in-memory CSRF token so a subsequent login gets a fresh one.
    clearCsrfToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, verify }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
