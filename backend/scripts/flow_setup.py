from datetime import date

from sqlalchemy.orm import joinedload

from backend.database import SessionLocal
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock


def prepare_demo_repas(profil_id: str) -> dict[str, str]:
    db = SessionLocal()
    try:
        recette = (
            db.query(Recette)
            .options(joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient))
            .filter(Recette.nom == "romazava")
            .one()
        )
        by_nom = {ligne.ingredient.nom: ligne.ingredient for ligne in recette.ingredients}

        stock = Stock(profil_id=profil_id, lieu_stockage="cuisine")
        db.add(stock)
        db.flush()
        qty = {
            "riz": 500.0,
            "poulet": 250.0,
            "bredes mafana": 50.0,
            "tomate": 200.0,
            "oignon": 200.0,
            "gingembre": 50.0,
        }
        for ligne in recette.ingredients:
            db.add(
                IngredientStock(
                    stock_id=stock.id,
                    ingredient_id=ligne.ingredient_id,
                    quantite_disponible=qty.get(ligne.ingredient.nom, 200.0),
                    unite=ligne.unite,
                )
            )

        planning = Planning(profil_id=profil_id, periode="semaine", date_debut=date.today())
        db.add(planning)
        db.flush()
        repas = RepasPlanifie(
            planning_id=planning.id,
            recette_id=recette.id,
            jour=date.today(),
            type_repas="dejeuner",
        )
        db.add(repas)
        db.commit()
        return {
            "planning_id": planning.id,
            "repas_id": repas.id,
            "riz_id": by_nom["riz"].id,
            "poulet_id": by_nom["poulet"].id,
            "bredes_id": by_nom["bredes mafana"].id,
        }
    finally:
        db.close()
