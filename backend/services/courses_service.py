from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.schemas.composites import ListeCoursesItem
from backend.schemas.ingredient import IngredientOut
from backend.services.stock_service import get_stock_profil


def get_liste_courses(db: Session, planning_id: str) -> list[ListeCoursesItem]:
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
        for ligne in get_stock_profil(db, planning.profil_id)
    }

    items = []
    for ingredient_id, poids_total in sorted(
        requis.items(), key=lambda item: ingredients_map[item[0]].nom
    ):
        disponible = stock_dispo.get(ingredient_id, 0.0)
        items.append(
            ListeCoursesItem(
                ingredient=IngredientOut.model_validate(ingredients_map[ingredient_id]),
                poids_total_requis=round(poids_total, 2),
                stock_disponible=round(disponible, 2),
                statut="disponible" if disponible >= poids_total else "à acheter",
            )
        )
    return items
