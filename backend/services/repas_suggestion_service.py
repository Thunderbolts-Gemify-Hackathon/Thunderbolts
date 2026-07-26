"""Suggestion d'un repas unique ("je veux manger quelque chose") : filtrage règles +
couverture stock déterministes, puis Gemma choisit parmi les candidats fournis
(jamais d'invention de recette_id, conforme à RULE_OWN_DATA)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.models.recette import Recette
from backend.services import onboarding_suite, recipe_rag
from backend.services.gemma_client import GemmaClient
from backend.services.prompts import build_system_prompt
from backend.services.stock_service import get_stock_profil

POOL_SIZE = 6


def inferer_type_repas(heure: int) -> str:
    if heure < 10:
        return "petit_dejeuner"
    if heure < 16:
        return "dejeuner"
    return "diner"


def suggerer_repas(
    db: Session,
    profil_id: str,
    type_repas: str | None,
    duree_max_minutes: int | None,
) -> dict[str, Any]:
    type_repas = type_repas or inferer_type_repas(datetime.now().hour)

    profil_complet = onboarding_suite.get_profil_complet(db, profil_id)
    preferences = dict(profil_complet.get("preferences") or {})
    preferences["objectif"] = (profil_complet.get("profil") or {}).get("objectif")

    corpus = recipe_rag.charger_corpus_recettes(db)
    compatibles = recipe_rag.filtrer_recettes_compatibles(
        corpus, preferences=preferences, foyer=profil_complet.get("foyer") or {}
    )

    candidats = [r for r in compatibles if type_repas in r["tags"]] or compatibles
    if duree_max_minutes:
        sous_temps = [
            r for r in candidats if (r.get("duree_minutes") or 0) <= duree_max_minutes
        ]
        candidats = sous_temps or candidats
    if not candidats:
        raise ValueError("Aucune recette compatible avec les allergies/tabous du profil")

    stock_dispo = {
        ligne.ingredient_id: float(ligne.quantite_disponible)
        for ligne in get_stock_profil(db, profil_id)
    }
    scored = sorted(
        (_avec_couverture(r, stock_dispo) for r in candidats),
        key=lambda r: -r["_couverture"],
    )
    pool = scored[:POOL_SIZE]

    choix = _demander_choix_gemma(profil_complet, pool, type_repas)
    pool_ids = {r["id"] for r in pool}
    if choix and choix.get("recette_id") in pool_ids:
        retenue = next(r for r in pool if r["id"] == choix["recette_id"])
        message = str(choix.get("message") or _message_par_defaut(retenue))
    else:
        retenue = pool[0]
        message = _message_par_defaut(retenue)

    recette_obj = db.get(Recette, retenue["id"])
    return {
        "recette": recette_obj,
        "type_repas": type_repas,
        "message": message,
        "couverture_stock": round(retenue["_couverture"], 2),
        "ingredients_manquants": retenue["_manquants"],
    }


def _avec_couverture(recette: dict[str, Any], stock_dispo: dict[str, float]) -> dict[str, Any]:
    lignes = recette["ingredients"]
    if not lignes:
        return {**recette, "_couverture": 1.0, "_manquants": []}
    manquants = []
    couverts = 0
    for ligne in lignes:
        if stock_dispo.get(ligne["ingredient_id"], 0.0) >= ligne["poids_requis"]:
            couverts += 1
        else:
            manquants.append(ligne["nom"])
    return {**recette, "_couverture": couverts / len(lignes), "_manquants": manquants}


def _message_par_defaut(recette: dict[str, Any]) -> str:
    if recette["_couverture"] >= 0.999:
        return f"{recette['nom']} : tu as deja tout ce qu'il faut en stock."
    manquants = ", ".join(recette["_manquants"][:3])
    return f"{recette['nom']} : il te manque {manquants} en stock."


def _demander_choix_gemma(
    profil_complet: dict[str, Any],
    pool: list[dict[str, Any]],
    type_repas: str,
) -> dict[str, Any] | None:
    candidats_json = json.dumps(
        [
            {
                "recette_id": r["id"],
                "nom": r["nom"],
                "kcal_total": r["kcal_total"],
                "duree_minutes": r.get("duree_minutes"),
                "couverture_stock": round(r["_couverture"], 2),
                "ingredients_manquants": r["_manquants"],
            }
            for r in pool
        ],
        ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": build_system_prompt(profil_complet)},
        {
            "role": "user",
            "content": (
                f"L'utilisateur veut manger maintenant (creneau {type_repas}). Choisis UNE "
                "recette parmi cette liste JSON — n'invente jamais de recette_id hors de "
                "cette liste — en privilegiant une bonne couverture_stock et peu "
                f"d'ingredients_manquants. Candidats : {candidats_json}\n\n"
                'Reponds UNIQUEMENT avec un JSON de la forme '
                '{"recette_id": "...", "message": "<1-2 phrases motivant ce choix, en '
                'francais>"}, sans texte ni markdown autour.'
            ),
        },
    ]
    try:
        result = GemmaClient().chat(messages)
    except RuntimeError:
        return None
    content = result["message"].get("content") or ""
    return _parse_choix_json(content)


def _parse_choix_json(content: str) -> dict[str, Any] | None:
    texte = (content or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", texte)
    if fence:
        texte = fence.group(1).strip()

    data = _loads_or_none(texte)
    if data is None:
        match = re.search(r"\{[\s\S]*\}", texte)
        if not match:
            return None
        data = _loads_or_none(match.group(0))

    return data if isinstance(data, dict) and data.get("recette_id") else None


def _loads_or_none(texte: str) -> Any | None:
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        return None
