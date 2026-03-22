import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import client from '../api/client'

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
    setUser(response.data.user || response.data)
    return response.data
  }

  const logout = async () => {
    try {
      await client.post('/accounts/logout/')
    } catch {
      // ignore logout errors
    }
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
