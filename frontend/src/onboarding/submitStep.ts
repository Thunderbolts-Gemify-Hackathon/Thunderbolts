import {
  createBudget,
  createFoyer,
  createLocalisation,
  createPreferences,
  createProfil,
  QUARTIER_COORDS,
} from "@/api/onboarding";
import { createUtilisateur } from "@/api/utilisateur";
import type { Session } from "@/session/SessionContext";

import type { OnboardingData, StepId } from "./types";

type Result = {
  /** Remplace toute la session (ex. après création compte). */
  session?: Session;
  /** Fusionne dans la session existante (ex. profilId). */
  sessionPatch?: Partial<Session>;
};

function requireSession(session: Session | null): Session {
  if (!session?.apiToken || !session.utilisateurId) {
    throw new Error("Crée d’abord ton compte (étape précédente).");
  }
  return session;
}

function requireProfilId(session: Session): string {
  if (!session.profilId) {
    throw new Error("Crée d’abord ton profil (étape précédente).");
  }
  return session.profilId;
}

/** Appels backend par étape d’onboarding. */
export async function submitStep(
  stepId: StepId,
  data: OnboardingData,
  session: Session | null
): Promise<Result> {
  if (stepId === "compte") {
    const c = data.compte;
    if (!c.nom.trim() || !c.prenom.trim() || !c.email.trim() || !c.date_naissance.trim()) {
      throw new Error("Remplis nom, prénom, email et date de naissance.");
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(c.date_naissance)) {
      throw new Error("Date de naissance au format AAAA-MM-JJ.");
    }

    const user = await createUtilisateur({
      nom: c.nom.trim(),
      prenom: c.prenom.trim(),
      email: c.email.trim().toLowerCase(),
      date_naissance: c.date_naissance.trim(),
    });

    return {
      session: {
        utilisateurId: user.id,
        apiToken: user.api_token,
        prenom: user.prenom,
        email: user.email,
      },
    };
  }

  if (stepId === "profil") {
    const s = requireSession(session);
    const p = data.profil;
    if (!p.sexe || !p.poids || !p.taille || !p.niveau_activite || !p.objectif) {
      throw new Error("Remplis sexe, poids, taille, activité et objectif.");
    }
    const poids = Number(p.poids);
    const taille = Number(p.taille);
    if (!Number.isFinite(poids) || poids <= 0 || !Number.isFinite(taille) || taille <= 0) {
      throw new Error("Poids et taille doivent être des nombres positifs.");
    }

    const profil = await createProfil(
      {
        utilisateur_id: s.utilisateurId,
        sexe: p.sexe,
        poids,
        taille,
        niveau_activite: p.niveau_activite,
        objectif: p.objectif,
      },
      s.apiToken
    );

    return { sessionPatch: { profilId: profil.id } };
  }

  if (stepId === "foyer") {
    const s = requireSession(session);
    const profilId = requireProfilId(s);
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
      // Backend : nombre_personnes >= membres + 1 (profil principal)
      if (nombre < 2) {
        throw new Error("Avec un membre, le foyer doit compter au moins 2 personnes.");
      }
      membres.push({
        prenom: f.membre_prenom.trim() || undefined,
        lien: f.membre_lien || undefined,
        age_approx: age,
      });
    }

    const foyer = await createFoyer(
      profilId,
      { nombre_personnes: nombre, membres },
      s.apiToken
    );

    return { sessionPatch: { foyerId: foyer.id } };
  }

  if (stepId === "preferences") {
    const s = requireSession(session);
    const profilId = requireProfilId(s);
    const p = data.preferences;

    const preferences = await createPreferences(
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

    return { sessionPatch: { preferencesId: preferences.id } };
  }

  if (stepId === "budget") {
    const s = requireSession(session);
    const profilId = requireProfilId(s);
    if (!s.preferencesId) {
      throw new Error("Enregistre d’abord tes préférences (étape précédente).");
    }

    const b = data.budget;
    const montant = Number(b.montant);
    if (!Number.isFinite(montant) || montant <= 0) {
      throw new Error("Indique un montant positif en Ariary.");
    }
    if (!["jour", "semaine", "mois"].includes(b.periode)) {
      throw new Error("Choisis une période (jour, semaine ou mois).");
    }

    const budget = await createBudget(
      profilId,
      { montant, periode: b.periode, devise: "Ar" },
      s.apiToken
    );

    return { sessionPatch: { budgetId: budget.id } };
  }

  if (stepId === "localisation") {
    const s = requireSession(session);
    const profilId = requireProfilId(s);
    const l = data.localisation;

    if (!l.quartier) {
      throw new Error("Choisis ton quartier.");
    }
    if (!l.saison || !["ete_humide", "hiver_sec", "intersaison"].includes(l.saison)) {
      throw new Error("Choisis une saison.");
    }

    const coords = QUARTIER_COORDS[l.quartier];
    if (!coords) {
      throw new Error("Quartier inconnu.");
    }

    const localisation = await createLocalisation(
      profilId,
      {
        latitude: coords.lat,
        longitude: coords.lon,
        quartier: l.quartier,
        saison: l.saison,
      },
      s.apiToken
    );

    return { sessionPatch: { localisationId: localisation.id } };
  }

  return {};
}
