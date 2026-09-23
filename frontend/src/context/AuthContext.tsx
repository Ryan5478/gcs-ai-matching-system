import { createContext, useContext, useState, ReactNode } from "react";
import api from "../api/client";

const AuthContext = createContext<any>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<any>(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });

  function persist(data: any) {
    localStorage.setItem("token", data.access_token);
    const u = { email: data.email, role: data.role, full_name: data.full_name };
    localStorage.setItem("user", JSON.stringify(u));
    setUser(u);
  }

  async function login(email: string, password: string) {
    const body = new URLSearchParams({ username: email, password });
    const { data } = await api.post("/auth/login", body);
    persist(data);
    return data;
  }

  async function register(payload: any) {
    const { data } = await api.post("/auth/register", payload);
    persist(data);
    return data;
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
