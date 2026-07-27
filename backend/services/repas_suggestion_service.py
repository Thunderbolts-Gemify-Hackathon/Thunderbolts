"""Suggestion d'un repas unique ("je veux manger quelque chose") : filtrage règles +
couverture stock déterministes, puis Gemma choisit parmi les candidats fournis
(jamais d'invention de recette_id, conforme à RULE_OWN_DATA)."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from backend.models.agent_action import AgentAction
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette
from backend.services import onboarding_suite, recipe_rag
from backend.services.gemma_client import GemmaClient
from backend.services.prompts import build_system_prompt
from backend.services.stock_coverage import avec_couverture, stock_map

POOL_SIZE = 6
_FEEDBACK_LIKE = 0.22
_FEEDBACK_DISLIKE = -0.35
_DIVERSITY_PENALTY = 0.1
_RANK_BLEND = 0.3
_RECENT_DAYS = 3


def inferer_type_repas(heure: int) -> str:
    if heure < 10:
        return "petit_dejeuner"
    if heure < 16:
        return "dejeuner"
    return "diner"


def _recent_suggested_ids(db: Session, profil_id: str) -> set[str]:
    """Recettes récemment suggérées (AgentAction) ou consommées (planning, 3 jours)."""
    ids: set[str] = set()
    cutoff = datetime.utcnow() - timedelta(days=_RECENT_DAYS)
    actions = (
        db.query(AgentAction)
        .filter(
            AgentAction.profil_id == profil_id,
            AgentAction.created_at >= cutoff,
        )
        .all()
    )
    for action in actions:
        try:
            payload = json.loads(action.payload_json or "{}")
        except json.JSONDecodeError:
            continue
        rid = payload.get("recette_id")
        if rid:
            ids.add(str(rid))

    jour_min = date.today() - timedelta(days=_RECENT_DAYS)
    rows = (
        db.query(RepasPlanifie.recette_id)
        .join(Planning, Planning.id == RepasPlanifie.planning_id)
        .filter(
            Planning.profil_id == profil_id,
            RepasPlanifie.statut == "consomme",
            RepasPlanifie.jour >= jour_min,
        )
        .all()
    )
    ids.update(r[0] for r in rows)
    return ids


def _candidats_scored(
    db: Session,
    profil_id: str,
    type_repas: str | None,
    duree_max_minutes: int | None,
    *,
    mode: str | None = None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    type_repas = type_repas or inferer_type_repas(datetime.now().hour)
    profil_complet = onboarding_suite.get_profil_complet(db, profil_id)
    preferences = dict(profil_complet.get("preferences") or {})
    preferences["objectif"] = (profil_complet.get("profil") or {}).get("objectif")

    recent_ids = _recent_suggested_ids(db, profil_id)
    corpus = recipe_rag.charger_corpus_recettes(db)
    compatibles = recipe_rag.rank_recettes(
        corpus,
        preferences=preferences,
        foyer=profil_complet.get("foyer") or {},
        recent_ids=recent_ids,
        duree_max=duree_max_minutes,
    )

    candidats = [r for r in compatibles if type_repas in r["tags"]] or compatibles
    if duree_max_minutes:
        sous_temps = [
            r for r in candidats if (r.get("duree_minutes") or 0) <= duree_max_minutes
        ]
        candidats = sous_temps or candidats
    if mode == "rapide":
        candidats = sorted(candidats, key=lambda r: r.get("duree_minutes") or 999)
    elif mode == "stock":
        pass  # tri couverture plus bas
    if not candidats:
        raise ValueError("Aucune recette compatible avec les allergies/tabous du profil")

    stock_dispo = stock_map(db, profil_id)
    scored = [avec_couverture(r, stock_dispo) for r in candidats]

    from backend.services import feedback_service

    liked = feedback_service.liked_recette_ids(db, profil_id)
    disliked = feedback_service.disliked_recette_ids(db, profil_id)

    rank_vals = [float(r.get("_rank_score") or 0) for r in scored]
    rank_max = max(rank_vals) if rank_vals else 0.0
    rank_min = min(rank_vals) if rank_vals else 0.0
    rank_span = (rank_max - rank_min) or 1.0

    for r in scored:
        bonus = 0.0
        if r["id"] in liked:
            bonus += _FEEDBACK_LIKE
        if r["id"] in disliked:
            bonus += _FEEDBACK_DISLIKE
        if r["id"] in recent_ids:
            bonus -= _DIVERSITY_PENALTY

        raw_rank = float(r.get("_rank_score") or 0)
        norm_rank = (raw_rank - rank_min) / rank_span
        r["_score"] = (
            float(r["_couverture"]) + bonus + _RANK_BLEND * norm_rank
        )

    if mode == "rapide":
        scored = sorted(
            scored, key=lambda r: (r.get("duree_minutes") or 999, -r["_score"])
        )
    else:
        scored = sorted(scored, key=lambda r: -r["_score"])
    return type_repas, scored, profil_complet


def suggerer_repas(
    db: Session,
    profil_id: str,
    type_repas: str | None,
    duree_max_minutes: int | None,
) -> dict[str, Any]:
    type_repas, scored, profil_complet = _candidats_scored(
        db, profil_id, type_repas, duree_max_minutes
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


def suggestion_ce_soir(
    db: Session,
    profil_id: str,
    *,
    mode: str | None = None,
    duree_max_minutes: int | None = None,
) -> dict[str, Any]:
    """Suggestion déterministe pour le dashboard (pas d'appel Gemma)."""
    from backend.services import llm_metrics

    type_repas, scored, _ = _candidats_scored(
        db, profil_id, None, duree_max_minutes, mode=mode or "stock"
    )
    retenue = scored[0]
    recette_obj = db.get(Recette, retenue["id"])
    cout = 0.0
    for ing in retenue.get("ingredients") or []:
        prix = float(ing.get("prix_moyen_reference") or 0)
        qty = float(ing.get("poids_requis") or 0)
        unite = (ing.get("unite") or "g").lower()
        if unite in ("g", "ml"):
            cout += prix * (qty / 1000.0)
        else:
            cout += prix * qty
    result = {
        "recette": recette_obj,
        "type_repas": type_repas,
        "message": _message_par_defaut(retenue),
        "couverture_stock": round(retenue["_couverture"], 2),
        "ingredients_manquants": retenue["_manquants"],
        "cout_estime": round(cout, 2),
        "alternatives": [
            {
                "recette_id": r["id"],
                "nom": r["nom"],
                "couverture_stock": round(r["_couverture"], 2),
                "duree_minutes": r.get("duree_minutes"),
            }
            for r in scored[1:4]
        ],
    }
    llm_metrics.record_event(
        "ce_soir",
        profil_id=profil_id,
        detail={"recette_id": retenue["id"], "type_repas": type_repas},
    )
    return result


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
