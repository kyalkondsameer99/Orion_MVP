"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

const STORAGE_KEY = "orion_user_id";

type UserIdContextValue = {
  userId: string | null;
  ready: boolean;
  setUserId: (id: string) => void;
};

const UserIdContext = createContext<UserIdContextValue | null>(null);

export function UserIdProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserIdState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const fromEnv = process.env.NEXT_PUBLIC_DEFAULT_USER_ID?.trim();
    let id = fromEnv || localStorage.getItem(STORAGE_KEY);
    if (!id) {
      id = crypto.randomUUID();
    }
    localStorage.setItem(STORAGE_KEY, id);
    setUserIdState(id);
    setReady(true);
  }, []);

  const setUserId = useCallback((id: string) => {
    const trimmed = id.trim();
    if (!trimmed) return;
    localStorage.setItem(STORAGE_KEY, trimmed);
    setUserIdState(trimmed);
  }, []);

  const value = useMemo(
    () => ({ userId, ready, setUserId }),
    [userId, ready, setUserId],
  );

  return <UserIdContext.Provider value={value}>{children}</UserIdContext.Provider>;
}

export function useUserId() {
  const ctx = useContext(UserIdContext);
  if (!ctx) {
    throw new Error("useUserId must be used within UserIdProvider");
  }
  return ctx;
}
