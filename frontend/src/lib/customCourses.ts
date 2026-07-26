import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";

import {
  createCourseItem,
  deleteCourseItem,
  listCourseItems,
  updateCourseItem,
  type ListeCourseItem,
} from "@/api/courses";

/**
 * Articles custom via API serveur, avec cache AsyncStorage de secours.
 */
const STORAGE_PREFIX = "kalitao.courses.custom.";

export type CustomCourseItem = {
  id: string;
  nom: string;
  fait: boolean;
  createdAt: number;
  ingredient_id?: string | null;
  quantite?: number;
  unite?: string;
};

function toLocal(item: ListeCourseItem): CustomCourseItem {
  return {
    id: item.id,
    nom: item.label,
    fait: item.coche || item.done,
    createdAt: Date.now(),
    ingredient_id: item.ingredient_id,
    quantite: item.quantite,
    unite: item.unite,
  };
}

async function cacheWrite(profilId: string, items: CustomCourseItem[]) {
  await AsyncStorage.setItem(STORAGE_PREFIX + profilId, JSON.stringify(items));
}

async function cacheRead(profilId: string): Promise<CustomCourseItem[]> {
  const raw = await AsyncStorage.getItem(STORAGE_PREFIX + profilId);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function useCustomCourses(
  profilId: string | undefined,
  token?: string | null
) {
  const [items, setItems] = useState<CustomCourseItem[]>([]);

  const reload = useCallback(async () => {
    if (!profilId) {
      setItems([]);
      return;
    }
    if (token) {
      try {
        const remote = await listCourseItems(profilId, token);
        const mapped = remote.map(toLocal);
        setItems(mapped);
        await cacheWrite(profilId, mapped);
        return;
      } catch {
        /* fallback cache */
      }
    }
    setItems(await cacheRead(profilId));
  }, [profilId, token]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const add = useCallback(
    async (nom: string) => {
      if (!profilId) return;
      const clean = nom.trim();
      if (!clean) return;
      if (token) {
        try {
          const created = await createCourseItem(profilId, token, {
            label: clean,
            custom: true,
          });
          const next = [...items.filter((i) => i.id !== created.id), toLocal(created)];
          setItems(next);
          await cacheWrite(profilId, next);
          return;
        } catch {
          /* offline: cache local */
        }
      }
      const current = await cacheRead(profilId);
      if (current.some((i) => i.nom.toLowerCase() === clean.toLowerCase())) return;
      const next = [
        ...current,
        {
          id: `local-${Date.now()}`,
          nom: clean,
          fait: false,
          createdAt: Date.now(),
        },
      ];
      await cacheWrite(profilId, next);
      setItems(next);
    },
    [profilId, token, items]
  );

  const toggle = useCallback(
    async (id: string) => {
      if (!profilId) return;
      const current = items;
      const target = current.find((i) => i.id === id);
      if (!target) return;
      const nextFait = !target.fait;
      if (token && !id.startsWith("local-")) {
        try {
          await updateCourseItem(profilId, token, id, { coche: nextFait });
        } catch {
          /* ignore */
        }
      }
      const next = current.map((i) =>
        i.id === id ? { ...i, fait: nextFait } : i
      );
      setItems(next);
      await cacheWrite(profilId, next);
    },
    [profilId, token, items]
  );

  const remove = useCallback(
    async (id: string) => {
      if (!profilId) return;
      if (token && !id.startsWith("local-")) {
        try {
          await deleteCourseItem(profilId, token, id);
        } catch {
          /* ignore */
        }
      }
      const next = items.filter((i) => i.id !== id);
      setItems(next);
      await cacheWrite(profilId, next);
    },
    [profilId, token, items]
  );

  return { items, add, toggle, remove, reload };
}
