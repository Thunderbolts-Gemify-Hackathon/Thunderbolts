"""Filtrage règles + tags des recettes (pas de RAG vectoriel — fallback assumé du workflow)."""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy.orm import Session, joinedload

from backend.models.recette import Recette, RecetteIngredient

MEAL_SLOTS = ("petit_dejeuner", "dejeuner", "diner")

OBJECTIF_TAG_PRIORITAIRE = {
    "perte_poids": "leger",
    "prise_masse": "riche",
}


def charger_corpus_recettes(db: Session) -> list[dict[str, Any]]:
    """Charge toutes les recettes du seed avec leurs tags, macros et ingrédients."""
    recettes = (
        db.query(Recette)
        .options(joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient))
        .all()
    )
    return [_serialize_recette(recette) for recette in recettes]


def _serialize_recette(recette: Recette) -> dict[str, Any]:
    return {
        "id": recette.id,
        "nom": recette.nom,
        "heure_conseillee": recette.heure_conseillee,
        "kcal_total": recette.kcal_total,
        "proteines": recette.proteines,
        "glucides": recette.glucides,
        "lipides": recette.lipides,
        "tags": list(recette.tags or []),
        "ingredients": [
            {
                "ingredient_id": ligne.ingredient_id,
                "nom": ligne.ingredient.nom,
                "poids_requis": ligne.poids_requis,
                "unite": ligne.unite,
            }
            for ligne in recette.ingredients
        ],
    }


def _noms_ingredients(recette: dict[str, Any]) -> set[str]:
    return {ligne["nom"].lower() for ligne in recette["ingredients"]}


def _ingredients_interdits(preferences: dict[str, Any], foyer: dict[str, Any]) -> set[str]:
    interdits = {
        nom.lower()
        for nom in (
            *(preferences.get("allergies") or []),
            *(preferences.get("tabous") or []),
            *(preferences.get("aliments_detestes") or []),
        )
    }
    # Restrictions individuelles des membres du foyer (ex. membre non aligné au régime
    # principal) : à exclure au même titre que les allergies du profil principal.
    for membre in (foyer or {}).get("membres") or []:
        restrictions = membre.get("restrictions") or ""
        interdits.update(nom.strip().lower() for nom in restrictions.split(",") if nom.strip())
    return interdits


def filtrer_recettes_compatibles(
    recettes: list[dict[str, Any]],
    preferences: dict[str, Any],
    foyer: dict[str, Any],
) -> list[dict[str, Any]]:
    """Exclut les recettes contenant un ingrédient interdit, puis priorise le tag lié à
    l'objectif du profil (ex : perte_poids -> tag "leger" en tête de liste)."""
    interdits = _ingredients_interdits(preferences, foyer)
    compatibles = [r for r in recettes if not (_noms_ingredients(r) & interdits)]

    tag_prioritaire = OBJECTIF_TAG_PRIORITAIRE.get(preferences.get("objectif") or "")
    if tag_prioritaire:
        compatibles.sort(key=lambda r: tag_prioritaire not in r["tags"])
    return compatibles


def selectionner_recettes_semaine(
    recettes_filtrees: list[dict[str, Any]], nb_jours: int
) -> list[dict[str, Any]]:
    """Choisit un repas par créneau (petit-déj/déjeuner/dîner) et par jour, sans répéter
    la même recette sur un créneau deux jours de suite."""
    par_creneau = {
        slot: [r for r in recettes_filtrees if slot in r["tags"]] for slot in MEAL_SLOTS
    }
    derniere_par_creneau: dict[str, str | None] = dict.fromkeys(MEAL_SLOTS)

    selection: list[dict[str, Any]] = []
    for _ in range(nb_jours):
        for slot in MEAL_SLOTS:
            candidats = par_creneau[slot] or recettes_filtrees
            if not candidats:
                continue
            choix = _choisir_sans_repetition(candidats, derniere_par_creneau[slot])
            derniere_par_creneau[slot] = choix["id"]
            selection.append(choix)
    return selection


def _choisir_sans_repetition(
    candidats: list[dict[str, Any]], derniere_id: str | None
) -> dict[str, Any]:
    pool = [c for c in candidats if c["id"] != derniere_id] or candidats
    return random.choice(pool)
