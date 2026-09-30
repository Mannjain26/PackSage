import { createContext, useContext, useState, type ReactNode } from 'react';
import { login as apiLogin, register as apiRegister } from '../services/authApi';

interface User { id: string; name: string; email: string; role: string; }
interface AuthCtx {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: { name: string; email: string; password: string; role?: string }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx>({} as AuthCtx);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(() => {
    try { return JSON.parse(localStorage.getItem('ps_user') || 'null'); } catch { return null; }
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('ps_token'));

  const login = async (email: string, password: string) => {
    const data = await apiLogin(email, password);
    localStorage.setItem('ps_token', data.access_token);
    const u: User = { id: data.user_id, name: data.name, email, role: data.role };
    localStorage.setItem('ps_user', JSON.stringify(u));
    setToken(data.access_token);
    setUser(u);
  };

  const register = async (payload: { name: string; email: string; password: string; role?: string }) => {
    await apiRegister(payload);
    await login(payload.email, payload.password);
  };

  const logout = () => {
    localStorage.removeItem('ps_token');
    localStorage.removeItem('ps_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
