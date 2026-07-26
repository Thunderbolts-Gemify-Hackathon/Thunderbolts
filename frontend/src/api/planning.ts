import { api } from "./http";
import type { Recette } from "./repas";

export type Repas = {
  id: string;
  jour: string;
  type_repas: string;
  statut: string;
  recette: Recette;
};

export const TYPE_REPAS_LABEL: Record<string, string> = {
  petit_dejeuner: "Petit-dejeuner",
  dejeuner: "Dejeuner",
  diner: "Diner",
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

export type PeriodeCourses = "jour" | "semaine" | "mois";

export type ListeCoursesPeriodeItem = {
  ingredient: { id: string; nom: string; unite_defaut: string; categorie?: string };
  categorie: string;
  quantite_totale_requise: number;
  quantite_disponible: number;
  quantite_a_acheter: number;
  unite: string;
  statut: "disponible" | "à acheter" | string;
};

export type EstimationCoutListe = {
  cout_total_estime: number;
  marches_a_visiter: { id: string; nom: string; type: string }[];
};

export type ListeCoursesPeriode = {
  periode: PeriodeCourses;
  date_debut: string;
  jours_couverts: number;
  items: ListeCoursesPeriodeItem[];
  estimation: EstimationCoutListe | null;
  message: string;
};

export function getListeCoursesPeriode(
  profilId: string,
  token: string,
  periode: PeriodeCourses,
  dateDebut: string,
  coords?: { lat: number; lon: number } | null
) {
  const q = new URLSearchParams({ periode, date_debut: dateDebut });
  if (coords) {
    q.set("lat", String(coords.lat));
    q.set("lon", String(coords.lon));
  }
  return api<ListeCoursesPeriode>(`/planning/${profilId}/liste-courses?${q}`, { token });
}

export function isAAcheter(statut: string) {
  return statut === "à acheter" || statut === "a acheter";
}

export function manquant(item: CourseItem) {
  return Math.max(0, item.poids_total_requis - item.stock_disponible);
}
