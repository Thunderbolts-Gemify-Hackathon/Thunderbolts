import { useCallback, useEffect, useState } from "react";

import { getEtapesRecette, type EtapeRecette } from "@/api/chat";
import { ApiError } from "@/api/http";
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
  const [etapes, setEtapes] = useState<EtapeRecette[] | null>(
    recetteId ? getCachedEtapes(recetteId) ?? null : null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEtapes = useCallback(async () => {
    if (!recetteId || !profilId || !token || loading) return;
    const cached = getCachedEtapes(recetteId);
    if (cached) {
      setEtapes(cached);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await getEtapesRecette(profilId, token, recetteId);
      cacheEtapes(recetteId, res.etapes);
      setEtapes(res.etapes);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Étapes indisponibles. Vérifie Ollama / Gemma.");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recetteId, profilId, token]);

  useEffect(() => {
    if (autoFetch) void fetchEtapes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoFetch]);

  return { etapes, loading, error, fetchEtapes };
}
