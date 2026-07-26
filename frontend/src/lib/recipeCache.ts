import type { Recette } from "@/api/repas";

/**
 * Les repas planifiés arrivent déjà avec leur recette complète imbriquée
 * (voir GET /planning/{profil_id}). Plutôt que d'ajouter un endpoint
 * GET /recettes/{id} juste pour re-fetcher ce qu'on a déjà, on garde une
 * référence en mémoire le temps de la navigation vers l'écran détail.
 */
export type CachedRepasContext = {
  repasId: string | null;
  statut: string | null;
  jour: string | null;
  typeRepas: string | null;
};

const recettes = new Map<string, Recette>();
const contexts = new Map<string, CachedRepasContext>();

export function cacheRecette(recette: Recette, context: CachedRepasContext = {
  repasId: null,
  statut: null,
  jour: null,
  typeRepas: null,
}) {
  recettes.set(recette.id, recette);
  contexts.set(recette.id, context);
}

export function getCachedRecette(id: string): Recette | undefined {
  return recettes.get(id);
}

export function getCachedContext(id: string): CachedRepasContext | undefined {
  return contexts.get(id);
}
