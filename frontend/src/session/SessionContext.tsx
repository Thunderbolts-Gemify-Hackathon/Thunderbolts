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

import {
  notifyAuthBundleChange,
  onAuthBundleChange,
  setAuthBundle,
} from "@/lib/authTokens";

const STORAGE_KEY = "kalitao.session";

export type Session = {
  utilisateurId: string;
  apiToken: string;
  /** JWT access (court). */
  accessToken?: string;
  /** JWT refresh (long). */
  refreshToken?: string;
  prenom: string;
  email: string;
  /** Profil personnel (onboarding). */
  profilId?: string;
  /**
   * Profil foyer actif pour stock/budget partagés.
   * Si absent, l'UI utilise profilId.
   */
  sharedProfilId?: string;
  foyerId?: string;
  preferencesId?: string;
  budgetId?: string;
  localisationId?: string;
  localisationLat?: number;
  localisationLon?: number;
};

type Ctx = {
  session: Session | null;
  ready: boolean;
  setSession: (s: Session) => Promise<void>;
  patchSession: (patch: Partial<Session>) => Promise<void>;
  clearSession: () => Promise<void>;
};

const SessionContext = createContext<Ctx | null>(null);

function syncAuthFromSession(s: Session | null) {
  setAuthBundle({
    apiToken: s?.apiToken ?? null,
    accessToken: s?.accessToken ?? null,
    refreshToken: s?.refreshToken ?? null,
  });
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSessionState] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((raw) => {
        if (raw) {
          const parsed = JSON.parse(raw) as Session;
          setSessionState(parsed);
          syncAuthFromSession(parsed);
        }
      })
      .finally(() => setReady(true));
  }, []);

  // Quand http.ts refresh un JWT, on persiste les nouveaux tokens.
  useEffect(() => {
    onAuthBundleChange((bundle) => {
      setSessionState((prev) => {
        if (!prev) return prev;
        const next: Session = {
          ...prev,
          apiToken: bundle.apiToken ?? prev.apiToken,
          accessToken: bundle.accessToken ?? undefined,
          refreshToken: bundle.refreshToken ?? undefined,
        };
        void AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        return next;
      });
    });
    return () => onAuthBundleChange(null);
  }, []);

  const setSession = useCallback(async (s: Session) => {
    setSessionState(s);
    syncAuthFromSession(s);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  }, []);

  const patchSession = useCallback(async (patch: Partial<Session>) => {
    setSessionState((prev) => {
      if (!prev) return prev;
      const next = { ...prev, ...patch };
      syncAuthFromSession(next);
      void AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clearSession = useCallback(async () => {
    setSessionState(null);
    syncAuthFromSession(null);
    notifyAuthBundleChange({
      apiToken: null,
      accessToken: null,
      refreshToken: null,
    });
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
