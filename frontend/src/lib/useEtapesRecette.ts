import { useCallback, useEffect, useState } from "react";

import { getEtapesRecette, type EtapeRecette } from "@/api/chat";
import { ApiError } from "@/api/http";
import { normalizeEtapes } from "@/lib/normalizeEtapes";
import { cacheEtapes, getCachedEtapes } from "@/lib/recipeCache";

/**
 * Étapes de recette générées par Gemma, partagées entre l'onglet "Instructions"
 * de l'écran détail et le mode cuisine plein écran (un seul appel réseau, pas un
 * par écran).
 */
export function useEtapesRecette(
  recetteId: string | undefined,
  profilId: string | undefined,
  token: string | undefined,
  autoFetch: boolean
) {
  const [etapes, setEtapes] = useState<EtapeRecette[] | null>(() => {
    if (!recetteId) return null;
    const cached = getCachedEtapes(recetteId);
    return Array.isArray(cached) && cached.length > 0 ? cached : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEtapes = useCallback(async () => {
    if (!recetteId || !profilId || !token) return;
    const cached = getCachedEtapes(recetteId);
    if (Array.isArray(cached) && cached.length > 0) {
      setEtapes(cached);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await getEtapesRecette(profilId, token, recetteId);
      const list = normalizeEtapes(res);
      if (list.length === 0) {
        setEtapes(null);
        setError("Aucune étape lisible. Réessaie dans un instant.");
        return;
      }
      cacheEtapes(recetteId, list);
      setEtapes(list);
    } catch (e) {
      setEtapes(null);
      setError(e instanceof ApiError ? e.detail : "Étapes indisponibles. Vérifie Ollama / Gemma.");
    } finally {
      setLoading(false);
    }
  }, [recetteId, profilId, token]);

  useEffect(() => {
    if (!autoFetch) return;
    void fetchEtapes();
  }, [autoFetch, fetchEtapes]);

  return { etapes, loading, error, fetchEtapes };
}
