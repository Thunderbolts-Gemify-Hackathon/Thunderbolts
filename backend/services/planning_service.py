from collections import defaultdict
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.schemas.composites import ListeCoursesItem
from backend.schemas.ingredient import IngredientOut
from backend.services import stock_service


def get_planning(
    db: Session,
    profil_id: str,
    periode: str,
    date_debut: date,
) -> Planning | None:
    return (
        db.query(Planning)
        .options(joinedload(Planning.repas).joinedload(RepasPlanifie.recette))
        .filter(
            Planning.profil_id == profil_id,
            Planning.periode == periode,
            Planning.date_debut == date_debut,
        )
        .first()
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
    """Passe le repas à consomme et décrémente le stock pour chaque RecetteIngredient."""
    repas = _repas_charge(db, repas_planifie_id)
    if repas.statut == "consomme":
        raise HTTPException(
            status_code=400,
            detail="Ce repas a déjà été validé",
        )
    if repas.statut == "annule":
        raise HTTPException(
            status_code=400,
            detail="Impossible de valider un repas annulé",
        )

    profil_id = repas.planning.profil_id
    for ligne in repas.recette.ingredients:
        stock_service.update_stock(
            db,
            profil_id,
            ligne.ingredient_id,
            ligne.poids_requis,
            commit=False,
        )

    repas.statut = "consomme"
    db.commit()
    db.refresh(repas)
    return repas


def annuler_validation(db: Session, repas_planifie_id: str) -> RepasPlanifie:
    """RF-12 : repasse à planifie et recrédite le stock."""
    repas = _repas_charge(db, repas_planifie_id)
    if repas.statut != "consomme":
        raise HTTPException(
            status_code=400,
            detail="Seule une validation (statut consomme) peut être annulée",
        )

    profil_id = repas.planning.profil_id
    for ligne in repas.recette.ingredients:
        stock_service.recrediter_stock(
            db,
            profil_id,
            ligne.ingredient_id,
            ligne.poids_requis,
            commit=False,
        )

    repas.statut = "planifie"
    db.commit()
    db.refresh(repas)
    return repas


def get_liste_courses(db: Session, planning_id: str) -> list[ListeCoursesItem]:
    """Agrège les RecetteIngredient du planning et compare au stock (RF-21/RF-22)."""
    planning = (
        db.query(Planning)
        .options(
            joinedload(Planning.repas)
            .joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient)
        )
        .filter(Planning.id == planning_id)
        .first()
    )
    if not planning:
        raise HTTPException(status_code=404, detail="Planning introuvable")

    requis: dict[str, float] = defaultdict(float)
    ingredients_map: dict[str, Ingredient] = {}
    for repas in planning.repas:
        if repas.statut == "annule":
            continue
        for ligne in repas.recette.ingredients:
            requis[ligne.ingredient_id] += ligne.poids_requis
            ingredients_map[ligne.ingredient_id] = ligne.ingredient

    stock_dispo = {
        ligne.ingredient_id: ligne.quantite_disponible
        for ligne in stock_service.get_stock_profil(db, planning.profil_id)
    }

    resultat: list[ListeCoursesItem] = []
    for ingredient_id, poids_total in sorted(
        requis.items(), key=lambda item: ingredients_map[item[0]].nom
    ):
        disponible = stock_dispo.get(ingredient_id, 0.0)
        statut = "disponible" if disponible >= poids_total else "à acheter"
        resultat.append(
            ListeCoursesItem(
                ingredient=IngredientOut.model_validate(ingredients_map[ingredient_id]),
                poids_total_requis=round(poids_total, 2),
                stock_disponible=round(disponible, 2),
                statut=statut,
            )
        )
    return resultat
