from sqlalchemy.orm import Session

from backend.data.catalog import INGREDIENTS, RECETTES
from backend.data.seed_helpers import get_or_create
from backend.models.ingredient import Ingredient
from backend.models.recette import Recette, RecetteIngredient


def seed_food(db: Session) -> dict:
    ingredients = {
        nom: get_or_create(db, Ingredient, {"nom": nom}, unite_defaut=unite)
        for nom, unite in INGREDIENTS.items()
    }
    for nom, (heure, kcal, prot, gluc, lip, tags, lignes) in RECETTES.items():
        recette = get_or_create(
            db,
            Recette,
            {"nom": nom},
            heure_conseillee=heure,
            kcal_total=kcal,
            proteines=prot,
            glucides=gluc,
            lipides=lip,
            tags=tags,
        )
        if not recette.ingredients:
            for ing_nom, poids, unite in lignes:
                db.add(
                    RecetteIngredient(
                        recette_id=recette.id,
                        ingredient_id=ingredients[ing_nom].id,
                        poids_requis=poids,
                        unite=unite,
                    )
                )
    return ingredients
