import { api } from "./http";

export type Repas = {
  id: string;
  jour: string;
  type_repas: string;
  statut: string;
  recette: { id: string; nom: string };
};

export type Planning = {
  id: string;
  periode: string;
  date_debut: string;
  repas: Repas[];
};

export type CourseItem = {
  ingredient: { id: string; nom: string; unite_defaut: string };
  poids_total_requis: number;
  stock_disponible: number;
  statut: "disponible" | "à acheter" | string;
};

export function getPlanning(
  profilId: string,
  token: string,
  dateDebut: string,
  periode = "semaine"
) {
  const q = new URLSearchParams({ periode, date_debut: dateDebut });
  return api<Planning>(`/planning/${profilId}?${q}`, { token });
}

export function generatePlanning(
  profilId: string,
  token: string,
  dateDebut: string,
  periode = "semaine"
) {
  const q = new URLSearchParams({ periode, date_debut: dateDebut });
  return api<Planning>(`/ia/${profilId}/generer-planning?${q}`, {
    method: "POST",
    token,
  });
}

export function validerRepas(repasId: string, token: string) {
  return api<Repas>(`/planning/${repasId}/valider`, { method: "POST", token });
}

export function annulerRepas(repasId: string, token: string) {
  return api<Repas>(`/planning/${repasId}/annuler`, { method: "POST", token });
}

export function getCourses(planningId: string, token: string) {
  return api<CourseItem[]>(`/planning/${planningId}/courses`, { token });
}

export function isAAcheter(statut: string) {
  return statut === "à acheter" || statut === "a acheter";
}

export function manquant(item: CourseItem) {
  return Math.max(0, item.poids_total_requis - item.stock_disponible);
}
