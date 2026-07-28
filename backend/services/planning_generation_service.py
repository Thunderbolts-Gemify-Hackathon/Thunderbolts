"""Orchestration : profil complet → recettes filtrées → Gemma (+ outils) → Planning."""

from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from backend.models.planning import Planning, RepasPlanifie
from backend.services import llm_metrics, onboarding_suite, planning_service, recipe_rag
from backend.services.gemma_agent import parse_json_list, run_tool_loop
from backend.services.gemma_client import GemmaClient
from backend.services.prompts import (
    CORRECTION_JSON,
    build_planning_user_prompt,
    build_system_prompt,
)
from backend.services.stock_coverage import avec_couverture, stock_map

JOURS_PAR_PERIODE = {"jour": 1, "semaine": 7, "mois": 30}
_W_COUVERTURE = 0.85
_CANDIDATS_PAR_CRENEAU = 10
_RECENT_PLANNING_DAYS = 14


def generer_planning(
    db: Session,
    profil_id: str,
    periode: str,
    date_debut: date,
    gemma_client: GemmaClient | None = None,
) -> Planning:
    """Génère un planning via Gemma à partir des recettes compatibles, puis le persiste.

    Pour `mois` : on demande seulement 7 jours à Gemma (fiable avec petits modèles),
    puis on répète le pattern hebdo sur 30 jours — même logique que la liste courses.
    """
    client = gemma_client or GemmaClient()
    nb_jours_total = JOURS_PAR_PERIODE.get(periode, 7)
    # Gemma ne génère jamais 90 repas d'un coup (gemma2:2b → JSON cassé → 422).
    nb_jours_ia = 7 if periode == "mois" else nb_jours_total
    t0 = time.perf_counter()

    try:
        profil_complet = onboarding_suite.get_profil_complet(db, profil_id)
        candidats = _selectionner_candidats(db, profil_id, profil_complet, nb_jours_ia)

        messages = [
            {"role": "system", "content": build_system_prompt(profil_complet)},
            {
                "role": "user",
                "content": build_planning_user_prompt(
                    nb_jours_ia, date_debut, candidats
                ),
            },
        ]
        # Pas d'outils ici : le stock est déjà injecté dans le prompt (couverture /
        # manquants). Laisser check_expiry/update_stock ferait dériver le petit modèle
        # et inventer des "manquants" incohérents.
        repas_json = _demander_planning_json(db, client, messages, profil_id)
        if periode == "mois":
            repas_json = _etendre_pattern_hebdo_json(
                repas_json, date_debut, nb_jours_total
            )

        planning = planning_service.create_planning_from_ia(
            db, profil_id, periode, date_debut, repas_json, candidats
        )
        llm_metrics.record_event(
            "planning_ok",
            profil_id=profil_id,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
        return planning
    except Exception as exc:
        llm_metrics.record_event(
            "planning_fail",
            profil_id=profil_id,
            latency_ms=(time.perf_counter() - t0) * 1000,
            detail=str(exc),
        )
        raise


def _etendre_pattern_hebdo_json(
    repas_semaine: list[dict[str, Any]],
    date_debut: date,
    nb_jours: int,
) -> list[dict[str, Any]]:
    """Répète les repas d'une semaine sur `nb_jours` (mois), en décalant les dates."""
    par_offset: dict[int, list[dict[str, Any]]] = {}
    for entree in repas_semaine:
        try:
            jour = date.fromisoformat(str(entree.get("jour", "")))
        except ValueError:
            continue
        offset = (jour - date_debut).days
        if offset < 0 or offset > 6:
            # Ancre relative au 1er jour présent si Gemma a décalé.
            continue
        par_offset.setdefault(offset, []).append(entree)

    if not par_offset:
        # Fallback : grouper par ordre d'apparition (0..6)
        for i, entree in enumerate(repas_semaine):
            par_offset.setdefault(i % 7, []).append(entree)

    etendu: list[dict[str, Any]] = []
    for jour_i in range(nb_jours):
        offset = jour_i % 7
        jour = date_debut + timedelta(days=jour_i)
        for modele in par_offset.get(offset, []):
            etendu.append(
                {
                    **modele,
                    "jour": jour.isoformat(),
                }
            )
    return etendu


def _recent_planning_ids(db: Session, profil_id: str) -> set[str]:
    cutoff = date.today() - timedelta(days=_RECENT_PLANNING_DAYS)
    rows = (
        db.query(RepasPlanifie.recette_id)
        .join(Planning, Planning.id == RepasPlanifie.planning_id)
        .filter(Planning.profil_id == profil_id, RepasPlanifie.jour >= cutoff)
        .all()
    )
    return {row[0] for row in rows if row[0]}


def _selectionner_candidats(
    db: Session,
    profil_id: str,
    profil_complet: dict[str, Any],
    nb_jours: int,
) -> list[dict[str, Any]]:
    preferences = dict(profil_complet.get("preferences") or {})
    preferences["objectif"] = (profil_complet.get("profil") or {}).get("objectif")

    compatibles = recipe_rag.rank_recettes(
        recipe_rag.charger_corpus_recettes(db),
        preferences=preferences,
        foyer=profil_complet.get("foyer") or {},
        recent_ids=_recent_planning_ids(db, profil_id),
    )
    if not compatibles:
        raise ValueError("Aucune recette compatible avec les allergies/tabous du profil")

    dispo = stock_map(db, profil_id)
    scores = [avec_couverture(r, dispo) for r in compatibles]
    for recette in scores:
        recette["_rank_score"] = float(recette.get("_rank_score") or 0) + (
            float(recette.get("_couverture") or 0) * _W_COUVERTURE
        )

    # Pool large par créneau (pas une semaine pré-figée) → Gemma peut vraiment varier.
    pool = recipe_rag.pool_candidats_planning(
        scores, par_creneau=_CANDIDATS_PAR_CRENEAU
    )
    if len(pool) < max(3, nb_jours):
        # Secours : ancienne sélection jour×créneau si le corpus est trop petit.
        scores.sort(
            key=lambda r: (-float(r.get("_rank_score") or 0), r.get("nom") or "")
        )
        return recipe_rag.selectionner_recettes_semaine(scores, nb_jours)
    return pool


def _demander_planning_json(
    db: Session,
    client: GemmaClient,
    messages: list[dict[str, Any]],
    profil_id: str,
) -> list[dict[str, Any]]:
    contenu = run_tool_loop(db, client, messages, profil_id=profil_id, tools=[])
    repas_json = parse_json_list(contenu)
    if repas_json is None:
        print(f"[planning] JSON invalide, 1er essai : {contenu[:500]!r}")
        messages.append({"role": "user", "content": CORRECTION_JSON})
        contenu = run_tool_loop(db, client, messages, profil_id=profil_id, tools=[])
        repas_json = parse_json_list(contenu)
    if repas_json is None:
        print(f"[planning] JSON invalide après retry : {contenu[:500]!r}")
        raise ValueError("Gemma n'a pas produit de planning JSON valide après retry")
    return repas_json
