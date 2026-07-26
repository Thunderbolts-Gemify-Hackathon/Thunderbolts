import { api } from "./http";

export type RecetteIngredient = {
  ingredient: { id: string; nom: string; unite_defaut: string };
  poids_requis: number;
  unite: string;
};

export type Recette = {
  id: string;
  nom: string;
  heure_conseillee?: string | null;
  kcal_total: number;
  proteines: number;
  glucides: number;
  lipides: number;
  duree_minutes?: number | null;
  tags: string[];
  instructions?: string | null;
  owner_profil_id?: string | null;
  ingredients: RecetteIngredient[];
};

export function listRecettes(
  token: string | null,
  opts?: {
    q?: string;
    tags?: string;
    max_duree?: number;
    profil_id?: string;
  }
) {
  const params = new URLSearchParams();
  if (opts?.q) params.set("q", opts.q);
  if (opts?.tags) params.set("tags", opts.tags);
  if (opts?.max_duree) params.set("max_duree", String(opts.max_duree));
  if (opts?.profil_id) params.set("profil_id", opts.profil_id);
  const qs = params.toString();
  return api<Recette[]>(`/recettes${qs ? `?${qs}` : ""}`, {
    token: token ?? undefined,
  });
}

export function getRecette(recetteId: string, token?: string | null) {
  return api<Recette>(`/recettes/${recetteId}`, {
    token: token ?? undefined,
  });
}
