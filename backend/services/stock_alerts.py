from collections import defaultdict
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock
from backend.schemas.composites import RuptureOut
from backend.schemas.ingredient import IngredientOut
from backend.services.stock_service import get_stock_profil


def detecter_ruptures(db: Session, profil_id: str, planning_id: str) -> list[RuptureOut]:
    planning = (
        db.query(Planning)
        .options(
            joinedload(Planning.repas)
            .joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient)
        )
        .filter(Planning.id == planning_id, Planning.profil_id == profil_id)
        .first()
    )
    if not planning:
        raise HTTPException(status_code=404, detail="Planning introuvable pour ce profil")

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
        for ligne in get_stock_profil(db, profil_id)
    }

    ruptures = []
    for ingredient_id, poids_requis in requis.items():
        manquant = poids_requis - stock_dispo.get(ingredient_id, 0.0)
        if manquant > 0:
            ruptures.append(
                RuptureOut(
                    ingredient=IngredientOut.model_validate(ingredients_map[ingredient_id]),
                    quantite_manquante=round(manquant, 2),
                )
            )
    return ruptures


def check_expiry(db: Session, profil_id: str, jours: int = 7) -> list[IngredientStock]:
    limite = date.today() + timedelta(days=jours)
    return [
        ligne
        for ligne in get_stock_profil(db, profil_id)
        if ligne.date_peremption is not None and ligne.date_peremption <= limite
    ]
