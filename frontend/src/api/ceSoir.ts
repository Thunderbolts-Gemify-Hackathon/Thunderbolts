import { api } from "./http";

export type CeSoirSuggestion = {
  recette: {
    id: string;
    nom: string;
    duree_minutes?: number | null;
    kcal_total?: number | null;
  };
  type_repas: string;
  message: string;
  couverture_stock: number;
  ingredients_manquants: string[];
  cout_estime: number;
  alternatives: {
    recette_id: string;
    nom: string;
    couverture_stock: number;
    duree_minutes?: number | null;
  }[];
};

export function getCeSoir(
  profilId: string,
  token: string,
  mode?: "stock" | "rapide"
) {
  const q = mode ? `?mode=${mode}` : "";
  return api<CeSoirSuggestion>(`/ia/${profilId}/ce-soir${q}`, { token });
}
