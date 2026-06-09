import { useState, createContext, useContext, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('jwt_token'))
  const [user,  setUser]  = useState(null)

  useEffect(() => {
    if (token) {
      try { setUser(JSON.parse(atob(token.split('.')[1]))) } catch {}
    }
  }, [token])

  const login  = (tok) => { localStorage.setItem('jwt_token', tok); setToken(tok) }
  const logout = ()    => { localStorage.removeItem('jwt_token'); setToken(null); setUser(null) }

  return <AuthContext.Provider value={{ token, user, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() { return useContext(AuthContext) }
