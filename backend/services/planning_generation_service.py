"""Orchestration bout-en-bout : profil complet -> Gemma (+ outils) -> Planning en base."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from sqlalchemy.orm import Session, joinedload

from backend.models.budget import Budget
from backend.models.foyer import Foyer
from backend.models.localisation import Localisation
from backend.models.planning import Planning, RepasPlanifie
from backend.models.preferences import Preferences
from backend.schemas.budget import BudgetOut
from backend.schemas.foyer import FoyerOut
from backend.schemas.localisation import LocalisationOut
from backend.schemas.preferences import PreferencesOut
from backend.services import onboarding_service, recipe_rag
from backend.services.gemma_client import GemmaClient
from backend.services.gemma_tools import TOOLS, execute_tool_call
from backend.services.prompts import build_system_prompt

MAX_TOOL_ITERATIONS = 5
JOURS_PAR_PERIODE = {"semaine": 7, "mois": 30}

CORRECTION_JSON = (
    "Le format de ta réponse précédente est invalide. Corrige et renvoie UNIQUEMENT un "
    'tableau JSON de la forme [{"jour": "AAAA-MM-JJ", "type_repas": '
    '"petit_dejeuner|dejeuner|diner", "recette_id": "..."}], sans texte ni markdown autour.'
)


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

    profil_complet = _charger_profil_complet(db, profil_id)
    corpus = recipe_rag.charger_corpus_recettes(db)
    compatibles = recipe_rag.filtrer_recettes_compatibles(
        corpus,
        preferences=_preferences_avec_objectif(profil_complet),
        foyer=profil_complet.get("foyer") or {},
    )
    if not compatibles:
        raise ValueError("Aucune recette compatible avec les allergies/tabous du profil")

    candidats = recipe_rag.selectionner_recettes_semaine(compatibles, nb_jours)

    messages = [
        {"role": "system", "content": build_system_prompt(profil_complet)},
        {"role": "user", "content": _message_generation(nb_jours, date_debut, candidats)},
    ]

    contenu = _executer_agent_loop(db, client, messages)
    repas_json = _parser_planning_json(contenu)
    if repas_json is None:
        messages.append({"role": "user", "content": CORRECTION_JSON})
        contenu = _executer_agent_loop(db, client, messages)
        repas_json = _parser_planning_json(contenu)
    if repas_json is None:
        raise ValueError("Gemma n'a pas produit de planning JSON valide après retry")

    return _creer_planning(db, profil_id, periode, date_debut, repas_json, candidats)


def _charger_profil_complet(db: Session, profil_id: str) -> dict[str, Any]:
    """Équivalent local de GET /onboarding/{id}/complet (Profil obligatoire, le reste optionnel)."""
    profil_out = onboarding_service.enrich_profil_out(onboarding_service.get_profil(db, profil_id))

    foyer = (
        db.query(Foyer)
        .options(joinedload(Foyer.membres))
        .filter(Foyer.profil_id == profil_id)
        .first()
    )
    preferences = db.query(Preferences).filter(Preferences.profil_id == profil_id).first()
    budget = (
        db.query(Budget).join(Preferences).filter(Preferences.profil_id == profil_id).first()
        if preferences
        else None
    )
    localisation = db.query(Localisation).filter(Localisation.profil_id == profil_id).first()

    return {
        "profil": profil_out.model_dump(),
        "foyer": FoyerOut.model_validate(foyer).model_dump() if foyer else None,
        "preferences": PreferencesOut.model_validate(preferences).model_dump() if preferences else None,
        "budget": BudgetOut.model_validate(budget).model_dump() if budget else None,
        "localisation": LocalisationOut.model_validate(localisation).model_dump() if localisation else None,
    }


def _preferences_avec_objectif(profil_complet: dict[str, Any]) -> dict[str, Any]:
    # recipe_rag priorise les tags selon l'objectif, qui vit sur Profil et non Preferences.
    preferences = dict(profil_complet.get("preferences") or {})
    preferences["objectif"] = (profil_complet.get("profil") or {}).get("objectif")
    return preferences


def _message_generation(nb_jours: int, date_debut: date, candidats: list[dict[str, Any]]) -> str:
    recettes_json = json.dumps(
        [
            {"recette_id": r["id"], "nom": r["nom"], "tags": r["tags"], "kcal_total": r["kcal_total"]}
            for r in candidats
        ],
        ensure_ascii=False,
    )
    return (
        f"Génère un planning de repas pour {nb_jours} jours à partir du {date_debut.isoformat()}, "
        "un repas par créneau (petit_dejeuner, dejeuner, diner) et par jour. "
        f"Choisis UNIQUEMENT parmi ces recettes (n'invente jamais de recette_id) : {recettes_json}\n\n"
        'Réponds UNIQUEMENT avec un tableau JSON de la forme [{"jour": "AAAA-MM-JJ", '
        '"type_repas": "petit_dejeuner|dejeuner|diner", "recette_id": "..."}], sans texte ni markdown autour.'
    )


def _executer_agent_loop(db: Session, client: GemmaClient, messages: list[dict[str, Any]]) -> str:
    """Boucle agent : exécute les tool calls de Gemma jusqu'à une réponse finale (5 tours max)."""
    for _ in range(MAX_TOOL_ITERATIONS):
        message = client.chat(messages, tools=TOOLS)["message"]
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return message.get("content") or ""

        messages.append({"role": "assistant", "content": message.get("content") or ""})
        for tool_call in tool_calls:
            resultat = execute_tool_call(db, tool_call["name"], tool_call.get("arguments") or {})
            messages.append(
                {
                    "role": "tool",
                    "name": tool_call["name"],
                    "content": json.dumps(resultat, ensure_ascii=False, default=str),
                }
            )

    raise RuntimeError("Limite d'itérations d'outils atteinte sans réponse finale de Gemma")


def _parser_planning_json(contenu: str) -> list[dict[str, Any]] | None:
    texte = (contenu or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", texte)
    if fence:
        texte = fence.group(1).strip()

    try:
        data = json.loads(texte)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", texte)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    return data if isinstance(data, list) else None


def _creer_planning(
    db: Session,
    profil_id: str,
    periode: str,
    date_debut: date,
    repas_json: list[dict[str, Any]],
    candidats: list[dict[str, Any]],
) -> Planning:
    ids_valides = {r["id"] for r in candidats}

    planning = Planning(profil_id=profil_id, periode=periode, date_debut=date_debut)
    db.add(planning)
    db.flush()

    repas_crees = 0
    for entree in repas_json:
        recette_id = entree.get("recette_id")
        type_repas = entree.get("type_repas")
        if recette_id not in ids_valides or not type_repas:
            continue  # recette hallucinée hors des candidats fournis : on l'ignore
        try:
            jour = date.fromisoformat(entree.get("jour", ""))
        except ValueError:
            continue

        db.add(
            RepasPlanifie(
                planning_id=planning.id,
                recette_id=recette_id,
                jour=jour,
                type_repas=type_repas,
            )
        )
        repas_crees += 1

    if repas_crees == 0:
        db.rollback()
        raise ValueError("Gemma n'a proposé aucun repas valide parmi les recettes candidates")

    db.commit()
    db.refresh(planning)
    return planning
