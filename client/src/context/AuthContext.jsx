import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../lib/apiClient'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('access_token') || null)
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user'))
    } catch {
      return null
    }
  })

  const [loading, setLoading] = useState(true)

  const login = useCallback((authRes) => {
    const userString = JSON.stringify(authRes.user)
    setToken(authRes.access_token)
    setUser(authRes.user)
    localStorage.setItem('access_token', authRes.access_token)
    localStorage.setItem('user', userString)
  }, [])

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }


  useEffect(() => {
    const initializeAuth = async () => {
      const localToken = localStorage.getItem('access_token')

      if (localToken) {
        try {
          const userData = await api.getCurrentUser()
          setUser(userData)
          localStorage.setItem('user', JSON.stringify(userData))
        } catch (e) {
          logout()
        }
      } else {
        try {
          const userData = await api.getCurrentUser()
          const userString = JSON.stringify(userData)
          const dummyToken = 'cookie_auth_user'

          setToken(dummyToken)
          setUser(userData)
          localStorage.setItem('access_token', dummyToken)
          localStorage.setItem('user', userString)

        } catch (e) {
        }
      }
      setLoading(false)
    }

    initializeAuth()
  }, [])

  return (
    <AuthContext.Provider value={{ token, user, setUser, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() { return useContext(AuthContext) }