import type { StepDef } from "./types";

export const STEPS: StepDef[] = [
  {
    id: "profil",
    title: "Ton profil",
    subtitle: "Pour des repas adaptés à ton objectif.",
    fields: [
      {
        key: "sexe",
        label: "Sexe",
        kind: "select",
        options: [
          { label: "Homme", value: "homme" },
          { label: "Femme", value: "femme" },
        ],
      },
      { key: "poids", label: "Poids (kg)", kind: "number", placeholder: "72" },
      { key: "taille", label: "Taille (cm)", kind: "number", placeholder: "175" },
      {
        key: "niveau_activite",
        label: "Activité",
        kind: "select",
        options: [
          { label: "Sédentaire", value: "sedentaire" },
          { label: "Léger", value: "leger" },
          { label: "Modéré", value: "modere" },
          { label: "Actif", value: "actif" },
        ],
      },
      {
        key: "objectif",
        label: "Objectif",
        kind: "select",
        options: [
          { label: "Perte de poids", value: "perte_poids" },
          { label: "Maintien", value: "maintien" },
          { label: "Prise de masse", value: "prise_masse" },
        ],
      },
    ],
  },
  {
    id: "foyer",
    title: "Ton foyer",
    subtitle: "Qui mange avec toi ?",
    fields: [
      {
        key: "nombre_personnes",
        label: "Nombre de personnes",
        kind: "number",
        placeholder: "2",
      },
      {
        key: "membre_prenom",
        label: "Prénom d’un membre",
        kind: "text",
        placeholder: "Voahirana",
      },
      {
        key: "membre_lien",
        label: "Lien",
        kind: "select",
        options: [
          { label: "Conjoint", value: "conjoint" },
          { label: "Enfant", value: "enfant" },
          { label: "Parent", value: "parent" },
          { label: "Autre", value: "autre" },
        ],
      },
      {
        key: "membre_age",
        label: "Âge approx.",
        kind: "number",
        placeholder: "25",
      },
    ],
  },
  {
    id: "preferences",
    title: "Goûts & limites",
    subtitle: "Rien de dangereux, rien de tabou.",
    fields: [
      {
        key: "allergies",
        label: "Allergies",
        kind: "chips",
        multi: true,
        options: [
          { label: "Arachide", value: "arachide" },
          { label: "Poisson", value: "poisson" },
          { label: "Gluten", value: "gluten" },
          { label: "Lactose", value: "lactose" },
        ],
      },
      {
        key: "tabous",
        label: "Tabous",
        kind: "chips",
        multi: true,
        options: [
          { label: "Porc", value: "porc" },
          { label: "Bœuf", value: "boeuf" },
          { label: "Canard", value: "canard" },
        ],
      },
      {
        key: "aliments_aimes",
        label: "Tu aimes",
        kind: "chips",
        multi: true,
        options: [
          { label: "Riz", value: "riz" },
          { label: "Poulet", value: "poulet" },
          { label: "Brèdes", value: "bredes mafana" },
          { label: "Poisson", value: "poisson" },
        ],
      },
      {
        key: "aliments_detestes",
        label: "Tu évites",
        kind: "chips",
        multi: true,
        options: [
          { label: "Gingembre", value: "gingembre" },
          { label: "Ail", value: "ail" },
          { label: "Pois chiches", value: "pois chiches" },
        ],
      },
    ],
  },
  {
    id: "budget",
    title: "Ton budget",
    subtitle: "En Ariary, pour rester réaliste.",
    fields: [
      {
        key: "montant",
        label: "Montant (Ar)",
        kind: "number",
        placeholder: "200000",
      },
      {
        key: "periode",
        label: "Période",
        kind: "select",
        options: [
          { label: "Jour", value: "jour" },
          { label: "Semaine", value: "semaine" },
          { label: "Mois", value: "mois" },
        ],
      },
    ],
  },
  {
    id: "localisation",
    title: "Ton quartier",
    subtitle: "Pour trouver les marchés près de chez toi.",
    fields: [
      {
        key: "quartier",
        label: "Quartier",
        kind: "select",
        options: [
          { label: "Analakely", value: "Analakely" },
          { label: "67ha", value: "67ha" },
          { label: "Ankorondrano", value: "Ankorondrano" },
          { label: "Andravoahangy", value: "Andravoahangy" },
        ],
      },
      {
        key: "saison",
        label: "Saison",
        kind: "select",
        options: [
          { label: "Été humide", value: "ete_humide" },
          { label: "Hiver sec", value: "hiver_sec" },
          { label: "Intersaison", value: "intersaison" },
        ],
      },
    ],
  },
];

export const STEP_IDS = STEPS.map((s) => s.id);

export function getStep(id: string): StepDef | undefined {
  return STEPS.find((s) => s.id === id);
}

export function stepIndex(id: string): number {
  return STEP_IDS.indexOf(id as (typeof STEP_IDS)[number]);
}

export function nextStepId(id: string): string | null {
  const i = stepIndex(id);
  return i >= 0 && i < STEP_IDS.length - 1 ? STEP_IDS[i + 1] : null;
}

export function prevStepId(id: string): string | null {
  const i = stepIndex(id);
  return i > 0 ? STEP_IDS[i - 1] : null;
}
