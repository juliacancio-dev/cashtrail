"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { apiClient, refreshAccessToken, setAccessToken } from "@/lib/api-client";

type User = {
  id: string;
  email: string;
  created_at: string;
};

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function loadCurrentUser(): Promise<void> {
    const response = await apiClient.get("/auth/me");
    setUser(response.ok ? ((await response.json()) as User) : null);
  }

  useEffect(() => {
    // Ao carregar a página, tenta renovar o access token a partir do cookie
    // httpOnly de refresh (silencioso) — ADR-006.
    (async () => {
      const refreshed = await refreshAccessToken();
      if (refreshed) await loadCurrentUser();
      setIsLoading(false);
    })();
  }, []);

  async function login(email: string, password: string): Promise<void> {
    const response = await apiClient.post("/auth/login", { email, password });
    if (!response.ok) {
      throw new Error("credenciais invalidas");
    }
    const data = (await response.json()) as { access_token: string };
    setAccessToken(data.access_token);
    await loadCurrentUser();
  }

  async function register(email: string, password: string): Promise<void> {
    const response = await apiClient.post("/auth/register", { email, password });
    if (!response.ok) {
      throw new Error(response.status === 409 ? "e-mail ja cadastrado" : "erro ao registrar");
    }
    await login(email, password);
  }

  async function logout(): Promise<void> {
    await apiClient.post("/auth/logout");
    setAccessToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}
