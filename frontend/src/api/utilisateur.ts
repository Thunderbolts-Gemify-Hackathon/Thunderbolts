import { api } from "./http";

export type UtilisateurCreate = {
  nom: string;
  prenom: string;
  email: string;
  date_naissance: string; // YYYY-MM-DD
};

export type Utilisateur = {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  date_naissance: string;
  api_token: string;
};

export function createUtilisateur(payload: UtilisateurCreate) {
  return api<Utilisateur>("/utilisateurs", { method: "POST", body: payload });
}
