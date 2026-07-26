from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.schemas.composites import ListeCoursesItem
from backend.schemas.ingredient import IngredientOut
from backend.services.stock_service import get_stock_profil
from backend.services.units import convert_quantity


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
    unite_requis: dict[str, str] = {}
    ingredients_map: dict[str, Ingredient] = {}
    for repas in planning.repas:
        if repas.statut == "annule":
            continue
        for ligne in repas.recette.ingredients:
            requis[ligne.ingredient_id] += ligne.poids_requis
            unite_requis[ligne.ingredient_id] = ligne.unite
            ingredients_map[ligne.ingredient_id] = ligne.ingredient

    stock_lignes = {
        ligne.ingredient_id: (float(ligne.quantite_disponible), ligne.unite)
        for ligne in get_stock_profil(db, planning.profil_id)
    }

    items = []
    for ingredient_id, poids_total in sorted(
        requis.items(), key=lambda item: ingredients_map[item[0]].nom
    ):
        unite = unite_requis.get(ingredient_id, ingredients_map[ingredient_id].unite_defaut)
        stock = stock_lignes.get(ingredient_id)
        if stock:
            disponible = convert_quantity(stock[0], stock[1], unite)
            if disponible is None:
                disponible = 0.0
        else:
            disponible = 0.0
        items.append(
            ListeCoursesItem(
                ingredient=IngredientOut.model_validate(ingredients_map[ingredient_id]),
                poids_total_requis=round(poids_total, 2),
                stock_disponible=round(disponible, 2),
                statut="disponible" if disponible + 1e-9 >= poids_total else "à acheter",
            )
        )
    return items
