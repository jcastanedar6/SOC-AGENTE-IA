import { createContext, useContext, useState, useCallback, useMemo } from "react"
import { STORAGE_KEY, USER_KEY } from "../constants"

const AuthContext = createContext(null)

function getStoredToken() {
  try { return localStorage.getItem(STORAGE_KEY) } catch { return null }
}

function getStoredUser() {
  try { return localStorage.getItem(USER_KEY) } catch { return null }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(getStoredToken)
  const [user, setUser] = useState(getStoredUser)

  const login = useCallback((newToken, newUser) => {
    localStorage.setItem(STORAGE_KEY, newToken)
    localStorage.setItem(USER_KEY, newUser)
    setToken(newToken)
    setUser(newUser)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
  }, [])

  const value = useMemo(() => ({ token, user, login, logout, isAuthenticated: !!token }), [token, user, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
