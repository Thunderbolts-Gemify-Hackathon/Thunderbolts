from datetime import date, time, timedelta

from backend.models.budget import Budget
from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.preferences import Preferences
from backend.models.profil import Profil
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock


def make_profil(db, **kwargs):
    data = {
        "age": 30,
        "sexe": "homme",
        "poids": 70.0,
        "taille": 175.0,
        "niveau_activite": "modere",
        "objectif": "maintien",
    }
    data.update(kwargs)
    profil = Profil(**data)
    db.add(profil)
    db.flush()
    return profil


def make_stock_profil(db, quantite_riz=500.0, quantite_poulet=100.0, with_budget=True):
    profil = make_profil(db)
    riz = Ingredient(nom="riz", unite_defaut="g")
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db.add_all([riz, poulet])
    db.flush()

    if with_budget:
        prefs = Preferences(profil_id=profil.id, tabous=[], allergies=[], aliments_detestes=[])
        db.add(prefs)
        db.flush()
        db.add(
            Budget(
                preferences_id=prefs.id,
                montant=100000,
                periode="semaine",
                montant_restant=100000,
            )
        )

    stock = Stock(profil_id=profil.id, lieu_stockage="cuisine")
    db.add(stock)
    db.flush()
    db.add_all(
        [
            IngredientStock(
                stock_id=stock.id,
                ingredient_id=riz.id,
                quantite_disponible=quantite_riz,
                unite="g",
                date_peremption=date.today() + timedelta(days=3),
            ),
            IngredientStock(
                stock_id=stock.id,
                ingredient_id=poulet.id,
                quantite_disponible=quantite_poulet,
                unite="g",
                date_peremption=date.today() + timedelta(days=30),
            ),
        ]
    )
    db.commit()
    return profil, riz, poulet


def make_planning_repas(db, profil, riz, poulet, qte_riz=500.0, qte_poulet=200.0):
    # stock already exists or caller creates it
    recette = Recette(nom="poulet riz", heure_conseillee=time(12, 0), kcal_total=600, tags=["dejeuner"])
    db.add(recette)
    db.flush()
    db.add_all(
        [
            RecetteIngredient(recette_id=recette.id, ingredient_id=riz.id, poids_requis=150.0, unite="g"),
            RecetteIngredient(recette_id=recette.id, ingredient_id=poulet.id, poids_requis=120.0, unite="g"),
        ]
    )
    planning = Planning(profil_id=profil.id, periode="semaine", date_debut=date.today())
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
    return planning, repas
