import { api } from "./http";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatResponse = {
  reponse: string;
  tool_calls: { name: string; arguments: Record<string, unknown>; result: unknown }[];
};

export type DirectiveCourses = {
  ingredient_id: string;
  ingredient_nom: string;
  point_de_vente: string;
  type_pdv: string;
  prix: number;
  devise: string;
  distance_km: number | null;
  niveau_securite: string | null;
  mode_deplacement: string | null;
  deprioritise: boolean;
  phrase: string;
};

export type RemedeResponse = {
  remede: string;
};

export function postChat(
  profilId: string,
  token: string,
  message: string,
  historique: ChatMessage[] = [],
  voice = false
) {
  return api<ChatResponse>(`/ia/${profilId}/chat`, {
    method: "POST",
    token,
    body: { message, historique, voice },
  });
}

export function postDirectiveCourses(
  profilId: string,
  token: string,
  ingredientNom: string
) {
  return api<DirectiveCourses>(`/ia/${profilId}/directive-courses`, {
    method: "POST",
    token,
    body: { ingredient_nom: ingredientNom },
  });
}

export function postSuggestionRemede(profilId: string, token: string) {
  return api<RemedeResponse>(`/ia/${profilId}/suggestion-remede`, {
    method: "POST",
    token,
  });
}

export type EtapeRecette = {
  numero: number;
  titre: string;
  ingredients: string[];
};

export type EtapesRecette = { etapes: EtapeRecette[] };

/**
 * Explication d'une recette en étapes courtes. Volontairement séparé de
 * postChat : pas d'outils, pas de boucle tool-calling — juste une question
 * directe à Gemma, bien plus fiable sur un petit modèle local.
 */
export function getEtapesRecette(profilId: string, token: string, recetteId: string) {
  return api<EtapesRecette>(`/ia/${profilId}/recette/${recetteId}/etapes`, {
    method: "POST",
    token,
  });
}
