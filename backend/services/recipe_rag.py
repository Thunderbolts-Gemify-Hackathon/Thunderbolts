"""Filtrage règles + ranking multi-signaux des recettes (pas de RAG vectoriel)."""

from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy.orm import Session, joinedload

from backend.models.recette import Recette, RecetteIngredient

MEAL_SLOTS = ("petit_dejeuner", "dejeuner", "diner")

OBJECTIF_TAG_PRIORITAIRE = {
    "perte_poids": "leger",
    "prise_masse": "riche",
}

# Soft-signal weights
_W_OBJECTIF = 2.0
_W_AIMES_PER = 0.8
_AIMES_CAP = 3
_W_JACCARD = 1.2
_W_DUREE = 0.5
_PENALTY_RECENT = 1.5


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
        "duree_minutes": recette.duree_minutes,
        "tags": list(recette.tags or []),
        "instructions": recette.instructions,
        "ingredients": [
            {
                "ingredient_id": ligne.ingredient_id,
                "nom": ligne.ingredient.nom,
                "poids_requis": ligne.poids_requis,
                "unite": ligne.unite,
                "prix_moyen_reference": ligne.ingredient.prix_moyen_reference,
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


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _compute_rank_score(
    recette: dict[str, Any],
    *,
    tag_prioritaire: str | None,
    aimes: set[str],
    recent_ids: set[str],
    duree_max: int | None,
) -> float:
    score = 0.0
    tags = recette.get("tags") or []
    if tag_prioritaire and tag_prioritaire in tags:
        score += _W_OBJECTIF

    ings = _noms_ingredients(recette)
    overlap = len(ings & aimes)
    score += _W_AIMES_PER * min(overlap, _AIMES_CAP)

    score += _jaccard(ings, aimes) * _W_JACCARD

    if duree_max is not None:
        duree = recette.get("duree_minutes")
        if duree is not None and duree <= duree_max:
            score += _W_DUREE

    if recette.get("id") in recent_ids:
        score -= _PENALTY_RECENT

    return score


def rank_recettes(
    recettes: list[dict[str, Any]],
    preferences: dict[str, Any],
    foyer: dict[str, Any],
    *,
    recent_ids: Iterable[str] | None = None,
    duree_max: int | None = None,
) -> list[dict[str, Any]]:
    """Hard-filter interdits, then soft multi-signal score → `_rank_score`.

    Sort déterministe : (-_rank_score, nom).
    """
    interdits = _ingredients_interdits(preferences, foyer)
    compatibles = [r for r in recettes if not (_noms_ingredients(r) & interdits)]

    tag_prioritaire = OBJECTIF_TAG_PRIORITAIRE.get(preferences.get("objectif") or "")
    aimes = {nom.lower() for nom in (preferences.get("aliments_aimes") or [])}
    recent = {str(rid) for rid in (recent_ids or [])}

    ranked: list[dict[str, Any]] = []
    for recette in compatibles:
        scored = dict(recette)
        scored["_rank_score"] = _compute_rank_score(
            recette,
            tag_prioritaire=tag_prioritaire,
            aimes=aimes,
            recent_ids=recent,
            duree_max=duree_max,
        )
        ranked.append(scored)

    ranked.sort(key=lambda r: (-r["_rank_score"], r.get("nom") or ""))
    return ranked


def filtrer_recettes_compatibles(
    recettes: list[dict[str, Any]],
    preferences: dict[str, Any],
    foyer: dict[str, Any],
    *,
    recent_ids: Iterable[str] | None = None,
    duree_max: int | None = None,
) -> list[dict[str, Any]]:
    """Exclut les interdits, puis ranking multi-signaux (alias de `rank_recettes`)."""
    return rank_recettes(
        recettes,
        preferences,
        foyer,
        recent_ids=recent_ids,
        duree_max=duree_max,
    )


def selectionner_recettes_semaine(
    recettes_filtrees: list[dict[str, Any]], nb_jours: int
) -> list[dict[str, Any]]:
    """Choisit un repas par créneau et par jour en privilégiant le score,
    en maximisant la diversité (évite les cycles A/B/A/B et les monos-plats)."""
    ordered = sorted(
        recettes_filtrees,
        key=lambda r: (
            -float(r.get("_rank_score") or 0),
            -float(r.get("_couverture") or 0),
            r.get("nom") or "",
        ),
    )
    par_creneau = {
        slot: [r for r in ordered if slot in (r.get("tags") or [])] for slot in MEAL_SLOTS
    }
    derniere_par_creneau: dict[str, str | None] = dict.fromkeys(MEAL_SLOTS)
    used_counts: dict[str, int] = {}

    selection: list[dict[str, Any]] = []
    for _ in range(nb_jours):
        for slot in MEAL_SLOTS:
            candidats = par_creneau[slot] or ordered
            if not candidats:
                continue
            choix = _choisir_diversifie(
                candidats, derniere_par_creneau[slot], used_counts
            )
            derniere_par_creneau[slot] = choix["id"]
            used_counts[choix["id"]] = used_counts.get(choix["id"], 0) + 1
            selection.append(choix)
    return selection


def pool_candidats_planning(
    recettes_filtrees: list[dict[str, Any]],
    *,
    par_creneau: int = 10,
) -> list[dict[str, Any]]:
    """Pool large pour Gemma : top N recettes par créneau, sans doublon d'id.

    Contrairement à `selectionner_recettes_semaine`, on ne pré-fixe pas le planning :
    le modèle choisit dans un menu varié (sinon 1 seul PD → kitoza tous les matins).
    """
    ordered = sorted(
        recettes_filtrees,
        key=lambda r: (
            -float(r.get("_rank_score") or 0),
            -float(r.get("_couverture") or 0),
            r.get("nom") or "",
        ),
    )
    seen: set[str] = set()
    pool: list[dict[str, Any]] = []
    for slot in MEAL_SLOTS:
        n_slot = 0
        for recette in ordered:
            if slot not in (recette.get("tags") or []):
                continue
            rid = recette["id"]
            if rid in seen:
                continue
            seen.add(rid)
            pool.append(recette)
            n_slot += 1
            if n_slot >= par_creneau:
                break
    return pool


def _choisir_diversifie(
    candidats: list[dict[str, Any]],
    derniere_id: str | None,
    used_counts: dict[str, int],
) -> dict[str, Any]:
    """Préfère les recettes peu utilisées, hors dernière, puis meilleur score."""

    def key(c: dict[str, Any]) -> tuple:
        return (
            used_counts.get(c["id"], 0),
            1 if c["id"] == derniere_id else 0,
            -float(c.get("_rank_score") or 0),
            -float(c.get("_couverture") or 0),
            c.get("nom") or "",
        )

    return min(candidats, key=key)


# Rétrocompat tests / imports
def _choisir_sans_repetition(
    candidats: list[dict[str, Any]], derniere_id: str | None
) -> dict[str, Any]:
    return _choisir_diversifie(candidats, derniere_id, {})
