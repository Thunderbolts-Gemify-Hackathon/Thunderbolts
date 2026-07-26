import {
  patchBudget,
  patchFoyer,
  patchLocalisation,
  patchPreferences,
  patchProfil,
  QUARTIER_COORDS,
} from "@/api/onboarding";
import type { Session } from "@/session/SessionContext";

import type { OnboardingData, StepId } from "./types";

type Result = {
  sessionPatch?: Partial<Session>;
  planningInvalide?: boolean;
};

function requireSession(session: Session | null): Session {
  if (!session?.apiToken || !session.utilisateurId || !session.profilId) {
    throw new Error("Session incomplete.");
  }
  return session;
}

/** Met à jour une étape déjà créée (PATCH), pour l'édition post-onboarding. */
export async function submitEditStep(
  stepId: StepId,
  data: OnboardingData,
  session: Session | null
): Promise<Result> {
  const s = requireSession(session);
  const profilId = s.profilId!;

  if (stepId === "profil") {
    const p = data.profil;
    if (!p.sexe || !p.poids || !p.taille || !p.niveau_activite || !p.objectif) {
      throw new Error("Remplis sexe, poids, taille, activité et objectif.");
    }
    const poids = Number(p.poids);
    const taille = Number(p.taille);
    if (!Number.isFinite(poids) || poids <= 0 || !Number.isFinite(taille) || taille <= 0) {
      throw new Error("Poids et taille doivent être des nombres positifs.");
    }
    const out = await patchProfil(
      profilId,
      {
        sexe: p.sexe,
        poids,
        taille,
        niveau_activite: p.niveau_activite,
        objectif: p.objectif,
      },
      s.apiToken
    );
    return { planningInvalide: Boolean(out.planning_invalide) };
  }

  if (stepId === "foyer") {
    const f = data.foyer;
    const nombre = Number(f.nombre_personnes);
    if (!Number.isFinite(nombre) || nombre < 1) {
      throw new Error("Indique un nombre de personnes valide (≥ 1).");
    }
    const membres = [];
    const age = Number(f.membre_age);
    if (f.membre_prenom.trim() || f.membre_lien || f.membre_age) {
      if (!Number.isFinite(age) || age < 0) {
        throw new Error("Âge du membre invalide.");
      }
      if (nombre < 2) {
        throw new Error("Avec un membre, le foyer doit compter au moins 2 personnes.");
      }
      membres.push({
        prenom: f.membre_prenom.trim() || undefined,
        lien: f.membre_lien || undefined,
        age_approx: age,
      });
    }
    const out = await patchFoyer(
      profilId,
      { nombre_personnes: nombre, membres },
      s.apiToken
    );
    return {
      sessionPatch: { foyerId: out.id },
      planningInvalide: Boolean(out.planning_invalide),
    };
  }

  if (stepId === "preferences") {
    const p = data.preferences;
    const out = await patchPreferences(
      profilId,
      {
        tabous: p.tabous,
        allergies: p.allergies,
        aliments_aimes: p.aliments_aimes,
        aliments_detestes: p.aliments_detestes,
        severite_allergie: p.allergies.length ? "moderee" : null,
        regime_specifique: p.tabous.includes("porc") ? "sans_porc" : "aucun",
      },
      s.apiToken
    );
    return {
      sessionPatch: { preferencesId: out.id },
      planningInvalide: Boolean(out.planning_invalide),
    };
  }

  if (stepId === "budget") {
    const b = data.budget;
    const montant = Number(b.montant);
    if (!Number.isFinite(montant) || montant <= 0) {
      throw new Error("Indique un montant positif en Ariary.");
    }
    if (!["jour", "semaine", "mois"].includes(b.periode)) {
      throw new Error("Choisis une période (jour, semaine ou mois).");
    }
    const out = await patchBudget(
      profilId,
      { montant, periode: b.periode, devise: "Ar" },
      s.apiToken
    );
    return {
      sessionPatch: { budgetId: out.id },
      planningInvalide: Boolean(out.planning_invalide),
    };
  }

  if (stepId === "localisation") {
    const l = data.localisation;
    if (!l.saison || !["ete_humide", "hiver_sec", "intersaison"].includes(l.saison)) {
      throw new Error("Choisis une saison.");
    }
    const gpsLat = Number(l.latitude);
    const gpsLon = Number(l.longitude);
    const hasGps =
      l.latitude !== "" &&
      l.longitude !== "" &&
      Number.isFinite(gpsLat) &&
      Number.isFinite(gpsLon);
    if (!hasGps && !l.quartier) {
      throw new Error("Choisis ton quartier ou utilise ta position.");
    }
    const coords = hasGps ? { lat: gpsLat, lon: gpsLon } : QUARTIER_COORDS[l.quartier];
    if (!coords) throw new Error("Quartier inconnu.");
    const out = await patchLocalisation(
      profilId,
      {
        latitude: coords.lat,
        longitude: coords.lon,
        quartier: l.quartier || undefined,
        saison: l.saison,
      },
      s.apiToken
    );
    return {
      sessionPatch: {
        localisationId: out.id,
        localisationLat: coords.lat,
        localisationLon: coords.lon,
      },
      planningInvalide: Boolean(out.planning_invalide),
    };
  }

  return {};
}
