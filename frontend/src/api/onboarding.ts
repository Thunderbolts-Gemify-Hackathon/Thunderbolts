import { api } from "./http";

export type ProfilCreate = {
  utilisateur_id: string;
  age?: number;
  sexe: string;
  poids: number;
  taille: number;
  niveau_activite: string;
  objectif: string;
  condition_sante?: string;
};

export type Profil = {
  id: string;
  utilisateur_id: string | null;
  age: number;
  sexe: string;
  poids: number;
  taille: number;
  niveau_activite: string;
  objectif: string;
  condition_sante: string | null;
  imc: number | null;
  besoin_calorique: number | null;
};

export function createProfil(payload: ProfilCreate, token: string) {
  return api<Profil>("/onboarding/profil", {
    method: "POST",
    body: payload,
    token,
  });
}

export type MembreFoyerCreate = {
  prenom?: string;
  lien?: string;
  age_approx: number;
  regime_aligne?: boolean;
  restrictions?: string;
};

export type FoyerCreate = {
  nombre_personnes: number;
  membres: MembreFoyerCreate[];
};

export type Foyer = {
  id: string;
  profil_id: string;
  nombre_personnes: number;
};

export function createFoyer(profilId: string, payload: FoyerCreate, token: string) {
  return api<Foyer>(`/onboarding/profil/${profilId}/foyer`, {
    method: "POST",
    body: payload,
    token,
  });
}

export type PreferencesCreate = {
  tabous: string[];
  allergies: string[];
  severite_allergie?: string | null;
  regime_specifique?: string | null;
  aliments_aimes: string[];
  aliments_detestes: string[];
};

export type Preferences = {
  id: string;
  profil_id: string;
};

export function createPreferences(
  profilId: string,
  payload: PreferencesCreate,
  token: string
) {
  return api<Preferences>(`/onboarding/profil/${profilId}/preferences`, {
    method: "POST",
    body: payload,
    token,
  });
}

export type BudgetCreate = {
  montant: number;
  periode: string;
  montant_restant?: number;
  devise?: string;
};

export type Budget = {
  id: string;
  preferences_id: string;
  montant: number;
  periode: string;
  montant_restant: number;
  devise: string;
};

export function createBudget(profilId: string, payload: BudgetCreate, token: string) {
  return api<Budget>(`/onboarding/profil/${profilId}/budget`, {
    method: "POST",
    body: payload,
    token,
  });
}

export type LocalisationCreate = {
  latitude: number;
  longitude: number;
  quartier?: string;
  saison?: string;
};

export type Localisation = {
  id: string;
  profil_id: string;
  latitude: number;
  longitude: number;
  quartier: string | null;
  saison: string | null;
};

export function createLocalisation(
  profilId: string,
  payload: LocalisationCreate,
  token: string
) {
  return api<Localisation>(`/onboarding/profil/${profilId}/localisation`, {
    method: "POST",
    body: payload,
    token,
  });
}

export type EtatDuJourType =
  | "fatigue"
  | "stresse"
  | "en_forme"
  | "un_peu_malade"
  | "normal";

export type EtatDuJour = {
  id: string;
  foyer_id: string;
  date: string;
  type: string;
};

export function createEtatDuJour(
  profilId: string,
  payload: { date: string; type: EtatDuJourType },
  token: string
) {
  return api<EtatDuJour>(`/onboarding/profil/${profilId}/etat-du-jour`, {
    method: "POST",
    body: payload,
    token,
  });
}

/** Coords démo Antananarivo par quartier (seed marchés). */
export const QUARTIER_COORDS: Record<string, { lat: number; lon: number }> = {
  Analakely: { lat: -18.9102, lon: 47.5256 },
  "67ha": { lat: -18.8792, lon: 47.521 },
  Ankorondrano: { lat: -18.8798, lon: 47.5219 },
  Andravoahangy: { lat: -18.9005, lon: 47.536 },
};
