"use client";

import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Role, User, USER_KEY, api } from "./api";

interface AuthContextType {
  user: User | null;
  login: (userId: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const HOME: Record<Role, string> = {
  patient: "/patient",
  asha: "/asha",
  pharmacist: "/pharmacist",
  district_officer: "/district",
};

/** Which roles may open a path. The report + case screens are shared by patients and their ASHA. */
export function allowed(path: string, role: Role): boolean {
  if (path.startsWith("/patient/report") || path.startsWith("/patient/cases")) return role === "patient" || role === "asha";
  if (path.startsWith("/patient")) return role === "patient";
  if (path.startsWith("/asha")) return role === "asha";
  if (path.startsWith("/pharmacist")) return role === "pharmacist";
  if (path.startsWith("/district")) return role === "district_officer";
  return true;
}

const PUBLIC = ["/", "/login"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(USER_KEY);
    } catch {
      /* no storage: stay logged out */
    }
    if (!stored) {
      setIsLoading(false); // eslint-disable-line react-hooks/set-state-in-effect -- one-time session restore
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => localStorage.removeItem(USER_KEY))
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(
    async (userId: string) => {
      localStorage.setItem(USER_KEY, userId);
      const me = await api.me();
      setUser(me);
      router.push(HOME[me.role]);
    },
    [router],
  );

  const logout = useCallback(() => {
    try {
      localStorage.removeItem(USER_KEY);
    } catch {
      /* ignore */
    }
    setUser(null);
    router.push("/login");
  }, [router]);

  useEffect(() => {
    if (isLoading) return;
    if (!user && !PUBLIC.includes(pathname)) router.replace("/login");
    else if (user && !allowed(pathname, user.role)) router.replace(HOME[user.role]);
  }, [user, isLoading, pathname, router]);

  return <AuthContext.Provider value={{ user, login, logout, isLoading }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
