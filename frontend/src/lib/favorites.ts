import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";

import { getFavori, toggleFavori as apiToggle } from "@/api/favoris";
import { useSession } from "@/session/SessionContext";

const STORAGE_KEY = "kalitao.favoris";

async function readLocal(): Promise<string[]> {
  const raw = await AsyncStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function writeLocal(ids: string[]) {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
}

export function useFavori(recetteId: string) {
  const { session } = useSession();
  const [favori, setFavori] = useState(false);
  const profilId = session?.profilId;
  const token = session?.apiToken;

  useEffect(() => {
    let mounted = true;
    (async () => {
      if (profilId && token && recetteId) {
        try {
          const r = await getFavori(profilId, token, recetteId);
          if (mounted) setFavori(r.favori);
          return;
        } catch {
          /* fallback local */
        }
      }
      const ids = await readLocal();
      if (mounted) setFavori(ids.includes(recetteId));
    })();
    return () => {
      mounted = false;
    };
  }, [recetteId, profilId, token]);

  const toggle = useCallback(async () => {
    if (profilId && token && recetteId) {
      try {
        const r = await apiToggle(profilId, token, recetteId);
        setFavori(r.favori);
        const ids = await readLocal();
        const next = r.favori
          ? [...new Set([...ids, recetteId])]
          : ids.filter((id) => id !== recetteId);
        await writeLocal(next);
        return;
      } catch {
        /* local fallback */
      }
    }
    const ids = await readLocal();
    const next = ids.includes(recetteId)
      ? ids.filter((id) => id !== recetteId)
      : [...ids, recetteId];
    await writeLocal(next);
    setFavori(next.includes(recetteId));
  }, [recetteId, profilId, token]);

  return { favori, toggle };
}
