import { api } from "./http";

export type UtilisateurCreate = {
  nom: string;
  prenom: string;
  email: string;
  date_naissance: string; // YYYY-MM-DD
  mot_de_passe: string;
};

export type UtilisateurLogin = {
  email: string;
  mot_de_passe: string;
};

export type Utilisateur = {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  date_naissance: string;
  api_token: string;
};

export type JwtLoginResult = {
  access_token: string;
  refresh_token: string;
  api_token: string;
  utilisateur: Utilisateur;
};

export function createUtilisateur(payload: UtilisateurCreate) {
  return api<Utilisateur>("/utilisateurs", { method: "POST", body: payload });
}

export function loginUtilisateur(payload: UtilisateurLogin) {
  return api<Utilisateur>("/utilisateurs/login", { method: "POST", body: payload });
}

/** Login avec access + refresh JWT (préféré). */
export function loginJwt(payload: UtilisateurLogin) {
  return api<JwtLoginResult>("/utilisateurs/login-jwt", {
    method: "POST",
    body: payload,
  });
}

export function refreshJwt(refreshToken: string) {
  return api<JwtLoginResult>("/utilisateurs/refresh", {
    method: "POST",
    body: { refresh_token: refreshToken },
    skipRefresh: true,
  });
}
