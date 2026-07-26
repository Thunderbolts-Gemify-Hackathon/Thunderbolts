from datetime import date
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.services import stock_service


def get_planning(
    db: Session, profil_id: str, periode: str, date_debut: date
) -> Planning | None:
    return (
        db.query(Planning)
        .options(
            joinedload(Planning.repas)
            .joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient)
        )
        .filter(
            Planning.profil_id == profil_id,
            Planning.periode == periode,
            Planning.date_debut == date_debut,
        )
        .first()
    )


def create_planning_from_ia(
    db: Session,
    profil_id: str,
    periode: str,
    date_debut: date,
    repas_json: list[dict[str, Any]],
    candidats: list[dict[str, Any]],
) -> Planning:
    """Persiste un planning IA en ignorant les recette_id hors candidats (anti-hallucination)."""
    ids_valides = {r["id"] for r in candidats}
    planning = Planning(profil_id=profil_id, periode=periode, date_debut=date_debut)
    db.add(planning)
    db.flush()

    repas_crees = 0
    for entree in repas_json:
        repas = _repas_depuis_entree_ia(planning.id, entree, ids_valides)
        if repas is None:
            continue
        db.add(repas)
        repas_crees += 1

    if repas_crees == 0:
        db.rollback()
        raise ValueError("Gemma n'a proposé aucun repas valide parmi les recettes candidates")

    db.commit()
    # Recharge avec repas + recette + ingrédients eager-load pour la sérialisation JSON.
    return get_planning(db, profil_id, periode, date_debut)


def _repas_depuis_entree_ia(
    planning_id: str,
    entree: dict[str, Any],
    ids_valides: set[str],
) -> RepasPlanifie | None:
    recette_id = entree.get("recette_id")
    type_repas = entree.get("type_repas")
    if recette_id not in ids_valides or not type_repas:
        return None
    try:
        jour = date.fromisoformat(entree.get("jour", ""))
    except ValueError:
        return None
    return RepasPlanifie(
        planning_id=planning_id,
        recette_id=recette_id,
        jour=jour,
        type_repas=type_repas,
    )


def _repas_charge(db: Session, repas_planifie_id: str) -> RepasPlanifie:
    repas = (
        db.query(RepasPlanifie)
        .options(
            joinedload(RepasPlanifie.planning),
            joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient),
        )
        .filter(RepasPlanifie.id == repas_planifie_id)
        .first()
    )
    if not repas:
        raise HTTPException(status_code=404, detail="Repas planifié introuvable")
    return repas


def valider_repas(db: Session, repas_planifie_id: str) -> RepasPlanifie:
    repas = _repas_charge(db, repas_planifie_id)
    if repas.statut == "consomme":
        raise HTTPException(status_code=400, detail="Ce repas a déjà été validé")
    if repas.statut == "annule":
        raise HTTPException(status_code=400, detail="Impossible de valider un repas annulé")

    for ligne in repas.recette.ingredients:
        stock_service.deduire_pour_recette(
            db,
            repas.planning.profil_id,
            ligne.ingredient_id,
            float(ligne.poids_requis),
            ligne.unite,
            commit=False,
        )
    repas.statut = "consomme"
    db.commit()
    db.refresh(repas)
    return repas


def annuler_validation(db: Session, repas_planifie_id: str) -> RepasPlanifie:
    repas = _repas_charge(db, repas_planifie_id)
    if repas.statut != "consomme":
        raise HTTPException(
            status_code=400, detail="Seule une validation (statut consomme) peut être annulée"
        )

    for ligne in repas.recette.ingredients:
        stock_service.recrediter_pour_recette(
            db,
            repas.planning.profil_id,
            ligne.ingredient_id,
            float(ligne.poids_requis),
            ligne.unite,
            commit=False,
        )
    repas.statut = "planifie"
    db.commit()
    db.refresh(repas)
    return repas
