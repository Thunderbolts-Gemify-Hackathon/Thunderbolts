"""Explication d'une recette en étapes, via un simple appel Gemma (sans outils).

Volontairement séparé de `run_tool_loop` / `/ia/{profil_id}/chat` : cette question
n'a besoin d'aucun outil (stock, marché, planning...), et sur un petit modèle local
(gemma2:2b) le laisser voir la liste complète des outils le fait parfois boucler
sans jamais produire de réponse finale (`RuntimeError`), ou répondre à côté.
Un appel direct, ciblé, est plus rapide et bien plus fiable pour ce cas précis.

Les étapes sont demandées en JSON structuré (pas du markdown à re-parser côté
client) pour permettre une navigation étape par étape fiable en mode cuisine.
"""

from __future__ import annotations

import re

import httpx
from sqlalchemy.orm import Session, joinedload

from backend.models.recette import Recette, RecetteIngredient
from backend.schemas.gemma import EtapeRecette
from backend.services.gemma_agent import parse_json_list
from backend.services.gemma_client import GemmaClient
from backend.services.prompts import build_etapes_system_prompt, build_etapes_user_prompt


def generer_etapes(
    db: Session,
    recette_id: str,
    client: GemmaClient | None = None,
) -> list[EtapeRecette]:
    recette = (
        db.query(Recette)
        .options(joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient))
        .filter(Recette.id == recette_id)
        .first()
    )
    if recette is None:
        raise ValueError("Recette introuvable")

    noms = [ligne.ingredient.nom for ligne in recette.ingredients]
    messages = [
        {"role": "system", "content": build_etapes_system_prompt()},
        {"role": "user", "content": build_etapes_user_prompt(recette.nom, noms)},
    ]

    try:
        resultat = (client or GemmaClient()).chat(messages, json_mode=True)
        contenu = ((resultat.get("message") or {}).get("content") or "").strip()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError):
        # Mode cuisine doit rester utilisable même si Ollama est down.
        return _etapes_fallback(recette.nom, noms)

    if not contenu:
        return _etapes_fallback(recette.nom, noms)

    etapes = _parse_etapes(contenu, noms)
    return etapes if etapes else _etapes_fallback(recette.nom, noms)


def _etapes_fallback(nom: str, noms_ingredients: list[str]) -> list[EtapeRecette]:
    """Étapes déterministes quand Gemma est indisponible ou illisible."""
    ingredients = list(noms_ingredients[:8])
    return [
        EtapeRecette(
            numero=1,
            titre=f"Rassembler les ingrédients pour {nom}.",
            ingredients=ingredients,
        ),
        EtapeRecette(
            numero=2,
            titre="Laver, couper et préparer ce qu'il faut.",
            ingredients=ingredients[:4],
        ),
        EtapeRecette(
            numero=3,
            titre=f"Cuisiner {nom} en suivant l'ordre habituel.",
            ingredients=[],
        ),
        EtapeRecette(
            numero=4,
            titre="Goûter, ajuster l'assaisonnement, puis servir.",
            ingredients=[],
        ),
    ]


def _unwrap_liste_etapes(brut: list) -> list:
    """Gemma renvoie parfois `{"etapes": [...]}` au lieu d'un tableau direct."""
    if (
        len(brut) == 1
        and isinstance(brut[0], dict)
        and isinstance(brut[0].get("etapes"), list)
    ):
        return brut[0]["etapes"]
    return brut


def _titre_lisible(valeur: object) -> str:
    """Refuse les titres qui ressemblent encore à du JSON brut ({, [, "titre")."""
    titre = str(valeur or "").strip()
    if not titre:
        return ""
    if titre[0] in "{[" or '"titre"' in titre or "'titre'" in titre:
        return ""
    # Coupe un éventuel préfixe markdown / numérotation déjà présent
    titre = re.sub(r"^\s*(?:\d+[.)]|[-*])\s*", "", titre).strip(" *\"'")
    return titre[:180]


def _parse_etapes(contenu: str, noms_ingredients: list[str]) -> list[EtapeRecette]:
    """JSON structuré en priorité ; repli sur un découpage markdown/numéroté si le
    modèle n'a pas respecté le format (garde la fonctionnalité utilisable quand même)."""
    canonique = {n.lower(): n for n in noms_ingredients}

    brut = parse_json_list(contenu)
    if brut:
        brut = _unwrap_liste_etapes(brut)
        etapes: list[EtapeRecette] = []
        for item in brut:
            if isinstance(item, str):
                titre = _titre_lisible(item)
                if titre:
                    etapes.append(
                        EtapeRecette(numero=len(etapes) + 1, titre=titre, ingredients=[])
                    )
                continue
            if not isinstance(item, dict):
                continue
            titre = _titre_lisible(
                item.get("titre")
                or item.get("titre_etape")
                or item.get("etape")
                or item.get("instruction")
                or item.get("description")
                or item.get("step")
                or item.get("texte")
            )
            if not titre:
                continue
            ingredients = _filtrer_ingredients(item.get("ingredients"), canonique)
            etapes.append(
                EtapeRecette(numero=len(etapes) + 1, titre=titre, ingredients=ingredients)
            )
        # Mode cuisine a besoin de plusieurs étapes. 1 seule = souvent du JSON
        # mal découpé → on préfère le texte ou le fallback déterministe.
        if len(etapes) >= 2:
            return etapes
        # 0 ou 1 étape JSON : ne pas tenter un découpage texte du blob JSON
        # (sinon on affiche des ``` / accolades). → fallback déterministe.
        if brut and _contenu_ressemble_json(contenu):
            return []

    texte = _parse_etapes_texte(contenu, canonique)
    if len(texte) >= 2:
        return texte
    return []


def _contenu_ressemble_json(contenu: str) -> bool:
    t = (contenu or "").strip()
    if t.startswith("```"):
        return True
    return t[:1] in "{["


def _filtrer_ingredients(valeurs: object, canonique: dict[str, str]) -> list[str]:
    if not isinstance(valeurs, list):
        return []
    vus: set[str] = set()
    resultat: list[str] = []
    for v in valeurs:
        nom = canonique.get(str(v).strip().lower())
        if nom and nom not in vus:
            vus.add(nom)
            resultat.append(nom)
    return resultat


_LIGNE_NUMEROTEE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s*(.+)$")


def _parse_etapes_texte(contenu: str, canonique: dict[str, str]) -> list[EtapeRecette]:
    """Dernier repli : le modèle a répondu en texte/markdown au lieu de JSON.
    On découpe par ligne numérotée/à puces. On n'affiche JAMAIS le JSON brut
    comme titre (sinon l'utilisateur voit des accolades)."""
    stripped = (contenu or "").strip()
    if stripped[:1] in "{[":
        # Bloc JSON illisible en tant que texte → laisser le fallback déterministe
        return []

    lignes = [l.strip(" *#") for l in stripped.splitlines() if l.strip()]
    etapes: list[EtapeRecette] = []
    for ligne in lignes:
        if ligne.startswith("```") or ligne[:1] in "{[" or '"titre"' in ligne:
            continue
        m = _LIGNE_NUMEROTEE.match(ligne)
        titre = _titre_lisible(m.group(1) if m else ligne)
        if not titre:
            continue
        etapes.append(EtapeRecette(numero=len(etapes) + 1, titre=titre, ingredients=[]))
    return etapes[:8]
