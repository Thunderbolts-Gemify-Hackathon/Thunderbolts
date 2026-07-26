import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";

/**
 * Articles ajoutés à la main à la liste de courses (en plus de ce que le
 * planning calcule automatiquement). Purement locaux, par profil : aucun
 * endpoint backend pour ça, pas de synchronisation entre appareils.
 */
const STORAGE_PREFIX = "kalitao.courses.custom.";

export type CustomCourseItem = {
  id: string;
  nom: string;
  fait: boolean;
  createdAt: number;
};

async function readAll(profilId: string): Promise<CustomCourseItem[]> {
  const raw = await AsyncStorage.getItem(STORAGE_PREFIX + profilId);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function writeAll(profilId: string, items: CustomCourseItem[]) {
  await AsyncStorage.setItem(STORAGE_PREFIX + profilId, JSON.stringify(items));
}

export function useCustomCourses(profilId: string | undefined) {
  const [items, setItems] = useState<CustomCourseItem[]>([]);

  const reload = useCallback(async () => {
    if (!profilId) {
      setItems([]);
      return;
    }
    setItems(await readAll(profilId));
  }, [profilId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const add = useCallback(
    async (nom: string) => {
      if (!profilId) return;
      const clean = nom.trim();
      if (!clean) return;
      const current = await readAll(profilId);
      if (current.some((i) => i.nom.toLowerCase() === clean.toLowerCase())) return;
      const next = [
        ...current,
        { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, nom: clean, fait: false, createdAt: Date.now() },
      ];
      await writeAll(profilId, next);
      setItems(next);
    },
    [profilId]
  );

  const toggle = useCallback(
    async (id: string) => {
      if (!profilId) return;
      const current = await readAll(profilId);
      const next = current.map((i) => (i.id === id ? { ...i, fait: !i.fait } : i));
      await writeAll(profilId, next);
      setItems(next);
    },
    [profilId]
  );

  const remove = useCallback(
    async (id: string) => {
      if (!profilId) return;
      const current = await readAll(profilId);
      const next = current.filter((i) => i.id !== id);
      await writeAll(profilId, next);
      setItems(next);
    },
    [profilId]
  );

  return { items, add, toggle, remove };
}
