import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { getCurrentUser, setAuthToken } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('story2art_token') || '');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      if (!token) {
        setUser(null);
        setAuthToken(null);
        setLoading(false);
        return;
      }

      setAuthToken(token);
      try {
        const { data } = await getCurrentUser();
        setUser(data);
      } catch (error) {
        setUser(null);
        setAuthToken(null);
        setToken('');
        localStorage.removeItem('story2art_token');
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, [token]);

  const login = async (authToken, userData) => {
    setToken(authToken);
    setAuthToken(authToken);
    setUser(userData);
    localStorage.setItem('story2art_token', authToken);
  };

  const logout = () => {
    setToken('');
    setUser(null);
    setAuthToken(null);
    localStorage.removeItem('story2art_token');
  };

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      login,
      logout,
      setUser,
    }),
    [token, user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
