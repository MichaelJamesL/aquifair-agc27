"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Role = "public" | "regulator" | "inspector" | "planner";

type RoleContextValue = {
  role: Role;
  setRole: (role: Role) => void;
};

const ROLE_STORAGE_KEY = "neraca.role";

const RoleContext = createContext<RoleContextValue | null>(null);

export const ROLE_LABELS: Record<Role, string> = {
  public: "Public viewer",
  regulator: "Bapenda · DPRD",
  inspector: "Dinas ESDM inspector",
  planner: "PDAM · Bappeda · PUPR",
};

export const ROLE_PEOPLE: Record<Role, { name: string; org: string; initials: string }> = {
  public: { name: "Public viewer", org: "Accounts and pipes by area", initials: "PV" },
  regulator: {
    name: "Dewi S.",
    org: "Bapenda Kota Semarang",
    initials: "DS",
  },
  inspector: {
    name: "Arif R.",
    org: "Inspector · Dinas ESDM Jateng",
    initials: "AR",
  },
  planner: {
    name: "Budi H.",
    org: "Bappeda Kota Semarang",
    initials: "BH",
  },
};

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>("regulator");

  useEffect(() => {
    const storedRole = window.localStorage.getItem(ROLE_STORAGE_KEY) as Role | null;
    if (storedRole && storedRole in ROLE_LABELS) setRoleState(storedRole);
  }, []);

  const value = useMemo<RoleContextValue>(
    () => ({
      role,
      setRole: (next) => {
        setRoleState(next);
        window.localStorage.setItem(ROLE_STORAGE_KEY, next);
      },
    }),
    [role],
  );

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}

export function useRole() {
  const value = useContext(RoleContext);
  if (!value) throw new Error("useRole must be used inside RoleProvider");
  return value;
}
