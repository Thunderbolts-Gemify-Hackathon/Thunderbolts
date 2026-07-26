import { api } from "./http";
import type { Ingredient } from "./stock";

export type TypeRepas = "petit_dejeuner" | "dejeuner" | "diner";

export type RecetteIngredientLigne = {
  ingredient: Ingredient;
  poids_requis: number;
  unite: string;
};

export type Recette = {
  id: string;
  nom: string;
  heure_conseillee: string | null;
  kcal_total: number;
  proteines: number;
  glucides: number;
  lipides: number;
  duree_minutes: number | null;
  tags: string[];
  instructions: string | null;
  ingredients: RecetteIngredientLigne[];
};

export type SuggestionRepas = {
  recette: Recette;
  type_repas: TypeRepas;
  message: string;
  couverture_stock: number;
  ingredients_manquants: string[];
};

export function inferTypeRepas(heure = new Date().getHours()): TypeRepas {
  if (heure < 10) return "petit_dejeuner";
  if (heure < 16) return "dejeuner";
  return "diner";
}

export function getSuggestionRepas(
  profilId: string,
  token: string,
  typeRepas: TypeRepas,
  dureeMaxMinutes: number | null
) {
  return api<SuggestionRepas>(`/ia/${profilId}/suggestion-repas`, {
    method: "POST",
    token,
    body: {
      type_repas: typeRepas,
      ...(dureeMaxMinutes ? { duree_max_minutes: dureeMaxMinutes } : {}),
    },
  });
}
