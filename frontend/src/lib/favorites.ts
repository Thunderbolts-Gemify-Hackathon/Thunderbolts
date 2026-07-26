import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";

/**
 * Favoris purement locaux (aucun endpoint backend pour ça) : persistés sur
 * l'appareil, pas synchronisés entre appareils. On ne fait pas semblant
 * que c'est plus que ça.
 */
const STORAGE_KEY = "kalitao.favoris";

async function readAll(): Promise<string[]> {
  const raw = await AsyncStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function useFavori(recetteId: string) {
  const [favori, setFavori] = useState(false);

  useEffect(() => {
    let mounted = true;
    readAll().then((ids) => {
      if (mounted) setFavori(ids.includes(recetteId));
    });
    return () => {
      mounted = false;
    };
  }, [recetteId]);

  const toggle = useCallback(async () => {
    const ids = await readAll();
    const next = ids.includes(recetteId)
      ? ids.filter((id) => id !== recetteId)
      : [...ids, recetteId];
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setFavori(next.includes(recetteId));
  }, [recetteId]);

  return { favori, toggle };
}
