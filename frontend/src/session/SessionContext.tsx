import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

const STORAGE_KEY = "kalitao.session";

export type Session = {
  utilisateurId: string;
  apiToken: string;
  prenom: string;
  email: string;
  profilId?: string;
  foyerId?: string;
  preferencesId?: string;
  budgetId?: string;
  localisationId?: string;
};

type Ctx = {
  session: Session | null;
  ready: boolean;
  setSession: (s: Session) => Promise<void>;
  patchSession: (patch: Partial<Session>) => Promise<void>;
  clearSession: () => Promise<void>;
};

const SessionContext = createContext<Ctx | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSessionState] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((raw) => {
        if (raw) setSessionState(JSON.parse(raw) as Session);
      })
      .finally(() => setReady(true));
  }, []);

  const setSession = useCallback(async (s: Session) => {
    setSessionState(s);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  }, []);

  const patchSession = useCallback(async (patch: Partial<Session>) => {
    setSessionState((prev) => {
      if (!prev) return prev;
      const next = { ...prev, ...patch };
      void AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clearSession = useCallback(async () => {
    setSessionState(null);
    await AsyncStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo(
    () => ({ session, ready, setSession, patchSession, clearSession }),
    [session, ready, setSession, patchSession, clearSession]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession hors SessionProvider");
  return ctx;
}
