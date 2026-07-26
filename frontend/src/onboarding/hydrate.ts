import type { ProfilCompletOut } from "@/api/onboarding";
import type { Session } from "@/session/SessionContext";

import { STEP_IDS } from "./steps";
import type { OnboardingData, StepId } from "./types";

export type HydrationResult = {
  data: Partial<OnboardingData>;
  sessionPatch: Partial<Session>;
  done: boolean;
  /** Prochaine étape d'onboarding à faire si `done` est faux. */
  resumeStep: StepId | null;
};

/**
 * Traduit la réponse de GET /onboarding/mine/complet en état local : ce qui
 * doit remplir le formulaire d'onboarding (`data`), ce qui doit rejoindre la
 * session (les ids), et si le parcours est terminé ou pas — pour ne plus
 * jamais dépendre d'un simple flag en mémoire qui disparaît au reload.
 */
export function hydrationFromComplet(complet: ProfilCompletOut): HydrationResult {
  const { profil, foyer, preferences, budget, localisation } = complet;

  const data: Partial<OnboardingData> = {
    profil: {
      sexe: profil.sexe ?? "",
      poids: profil.poids != null ? String(profil.poids) : "",
      taille: profil.taille != null ? String(profil.taille) : "",
      niveau_activite: profil.niveau_activite ?? "",
      objectif: profil.objectif ?? "",
    },
  };
  const sessionPatch: Partial<Session> = { profilId: profil.id };

  if (foyer) {
    const premier = foyer.membres[0];
    data.foyer = {
      nombre_personnes: String(foyer.nombre_personnes ?? ""),
      membre_prenom: premier?.prenom ?? "",
      membre_lien: premier?.lien ?? "",
      membre_age: premier ? String(premier.age_approx) : "",
    };
    sessionPatch.foyerId = foyer.id;
  }

  if (preferences) {
    data.preferences = {
      allergies: preferences.allergies ?? [],
      tabous: preferences.tabous ?? [],
      aliments_aimes: preferences.aliments_aimes ?? [],
      aliments_detestes: preferences.aliments_detestes ?? [],
    };
    sessionPatch.preferencesId = preferences.id;
  }

  if (budget) {
    data.budget = {
      montant: budget.montant != null ? String(budget.montant) : "",
      periode: budget.periode ?? "semaine",
    };
    sessionPatch.budgetId = budget.id;
  }

  if (localisation) {
    data.localisation = {
      quartier: localisation.quartier ?? "",
      saison: localisation.saison ?? "",
      latitude: String(localisation.latitude ?? ""),
      longitude: String(localisation.longitude ?? ""),
    };
    sessionPatch.localisationId = localisation.id;
    sessionPatch.localisationLat = localisation.latitude;
    sessionPatch.localisationLon = localisation.longitude;
  }

  const doneParEtape: Record<StepId, boolean> = {
    profil: true,
    foyer: Boolean(foyer),
    preferences: Boolean(preferences),
    budget: Boolean(budget),
    localisation: Boolean(localisation),
  };
  const premiereEtapeManquante = STEP_IDS.find((id) => !doneParEtape[id]) ?? null;

  return {
    data,
    sessionPatch,
    done: premiereEtapeManquante === null,
    resumeStep: premiereEtapeManquante,
  };
}
