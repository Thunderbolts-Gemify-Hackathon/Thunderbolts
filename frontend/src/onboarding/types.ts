export type StepId =
  | "profil"
  | "foyer"
  | "preferences"
  | "budget"
  | "localisation";

export type FieldKind = "text" | "email" | "number" | "select" | "chips" | "date" | "location";

export type FieldDef = {
  key: string;
  label: string;
  kind: FieldKind;
  placeholder?: string;
  options?: { label: string; value: string }[];
  multi?: boolean;
};

export type StepDef = {
  id: StepId;
  title: string;
  subtitle: string;
  fields: FieldDef[];
};

export type OnboardingData = {
  profil: {
    sexe: string;
    poids: string;
    taille: string;
    niveau_activite: string;
    objectif: string;
  };
  foyer: {
    nombre_personnes: string;
    membre_prenom: string;
    membre_lien: string;
    membre_age: string;
  };
  preferences: {
    allergies: string[];
    tabous: string[];
    aliments_aimes: string[];
    aliments_detestes: string[];
  };
  budget: {
    montant: string;
    periode: string;
  };
  localisation: {
    quartier: string;
    saison: string;
    /** Coordonnées GPS réelles (optionnelles) — remplacent le quartier si présentes. */
    latitude: string;
    longitude: string;
  };
};

export const initialData: OnboardingData = {
  profil: {
    sexe: "",
    poids: "",
    taille: "",
    niveau_activite: "",
    objectif: "",
  },
  foyer: {
    nombre_personnes: "",
    membre_prenom: "",
    membre_lien: "",
    membre_age: "",
  },
  preferences: {
    allergies: [],
    tabous: [],
    aliments_aimes: [],
    aliments_detestes: [],
  },
  budget: { montant: "", periode: "semaine" },
  localisation: { quartier: "", saison: "", latitude: "", longitude: "" },
};
