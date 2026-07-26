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
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise RuntimeError("Gemma indisponible (Ollama / API distante)") from exc

    contenu = (resultat.get("message") or {}).get("content") or ""
    contenu = contenu.strip()
    if not contenu:
        raise RuntimeError("Gemma n'a pas produit d'étapes pour cette recette")

    etapes = _parse_etapes(contenu, noms)
    if not etapes:
        raise RuntimeError("Réponse de Gemma illisible pour les étapes")
    return etapes


def _parse_etapes(contenu: str, noms_ingredients: list[str]) -> list[EtapeRecette]:
    """JSON structuré en priorité ; repli sur un découpage markdown/numéroté si le
    modèle n'a pas respecté le format (garde la fonctionnalité utilisable quand même)."""
    canonique = {n.lower(): n for n in noms_ingredients}

    brut = parse_json_list(contenu)
    if brut:
        etapes: list[EtapeRecette] = []
        for i, item in enumerate(brut, start=1):
            if not isinstance(item, dict):
                continue
            titre = str(item.get("titre") or item.get("titre_etape") or item.get("etape") or "").strip()
            if not titre:
                continue
            ingredients_bruts = item.get("ingredients")
            ingredients = _filtrer_ingredients(ingredients_bruts, canonique)
            etapes.append(EtapeRecette(numero=i, titre=titre, ingredients=ingredients))
        if etapes:
            return etapes

    return _parse_etapes_texte(contenu, canonique)


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
    On découpe par ligne numérotée/à puces, sans prétendre isoler les ingrédients
    par étape (mieux qu'un échec total)."""
    lignes = [l.strip(" *#") for l in contenu.splitlines() if l.strip()]
    etapes: list[EtapeRecette] = []
    for ligne in lignes:
        m = _LIGNE_NUMEROTEE.match(ligne)
        titre = m.group(1).strip(" *") if m else ligne
        if not titre:
            continue
        etapes.append(EtapeRecette(numero=len(etapes) + 1, titre=titre, ingredients=[]))
    if etapes:
        return etapes[:8]

    return [EtapeRecette(numero=1, titre=contenu.strip(), ingredients=list(canonique.values()))]
