"""Orchestration : profil complet → recettes filtrées → Gemma (+ outils) → Planning."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from backend.models.planning import Planning
from backend.services import onboarding_suite, planning_service, recipe_rag
from backend.services.gemma_agent import parse_json_list, run_tool_loop
from backend.services.gemma_client import GemmaClient
from backend.services.prompts import (
    CORRECTION_JSON,
    build_planning_user_prompt,
    build_system_prompt,
)

JOURS_PAR_PERIODE = {"jour": 1, "semaine": 7, "mois": 30}


def generer_planning(
    db: Session,
    profil_id: str,
    periode: str,
    date_debut: date,
    gemma_client: GemmaClient | None = None,
) -> Planning:
    """Génère un planning via Gemma à partir des recettes compatibles, puis le persiste."""
    client = gemma_client or GemmaClient()
    nb_jours = JOURS_PAR_PERIODE.get(periode, 7)

    profil_complet = onboarding_suite.get_profil_complet(db, profil_id)
    candidats = _selectionner_candidats(db, profil_complet, nb_jours)

    messages = [
        {"role": "system", "content": build_system_prompt(profil_complet)},
        {"role": "user", "content": build_planning_user_prompt(nb_jours, date_debut, candidats)},
    ]
    repas_json = _demander_planning_json(db, client, messages, profil_id)

    return planning_service.create_planning_from_ia(
        db, profil_id, periode, date_debut, repas_json, candidats
    )


def _selectionner_candidats(
    db: Session,
    profil_complet: dict[str, Any],
    nb_jours: int,
) -> list[dict[str, Any]]:
    preferences = dict(profil_complet.get("preferences") or {})
    preferences["objectif"] = (profil_complet.get("profil") or {}).get("objectif")

    compatibles = recipe_rag.filtrer_recettes_compatibles(
        recipe_rag.charger_corpus_recettes(db),
        preferences=preferences,
        foyer=profil_complet.get("foyer") or {},
    )
    if not compatibles:
        raise ValueError("Aucune recette compatible avec les allergies/tabous du profil")
    return recipe_rag.selectionner_recettes_semaine(compatibles, nb_jours)


def _demander_planning_json(
    db: Session,
    client: GemmaClient,
    messages: list[dict[str, Any]],
    profil_id: str,
) -> list[dict[str, Any]]:
    contenu = run_tool_loop(db, client, messages, profil_id=profil_id)
    repas_json = parse_json_list(contenu)
    if repas_json is None:
        print(f"[planning] JSON invalide, 1er essai : {contenu[:500]!r}")
        messages.append({"role": "user", "content": CORRECTION_JSON})
        contenu = run_tool_loop(db, client, messages, profil_id=profil_id)
        repas_json = parse_json_list(contenu)
    if repas_json is None:
        print(f"[planning] JSON invalide après retry : {contenu[:500]!r}")
        raise ValueError("Gemma n'a pas produit de planning JSON valide après retry")
    return repas_json
