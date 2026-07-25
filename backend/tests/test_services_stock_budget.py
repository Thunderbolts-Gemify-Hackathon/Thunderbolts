from datetime import date, time, timedelta

import pytest
from fastapi import HTTPException

from backend.models.budget import Budget
from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.preferences import Preferences
from backend.models.profil import Profil
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock
from backend.services import budget_service, stock_service


def _setup_profil_stock(db_session, quantite_riz=500.0, quantite_poulet=100.0):
    profil = Profil(
        age=30,
        sexe="homme",
        poids=70.0,
        taille=175.0,
        niveau_activite="modere",
        objectif="maintien",
    )
    riz = Ingredient(nom="riz", unite_defaut="g")
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add_all([profil, riz, poulet])
    db_session.flush()

    prefs = Preferences(profil_id=profil.id, tabous=[], allergies=[], aliments_detestes=[])
    db_session.add(prefs)
    db_session.flush()
    db_session.add(
        Budget(
            preferences_id=prefs.id,
            montant=100000,
            periode="semaine",
            montant_restant=100000,
        )
    )

    stock = Stock(profil_id=profil.id, lieu_stockage="cuisine")
    db_session.add(stock)
    db_session.flush()
    db_session.add_all(
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
    db_session.commit()
    return profil, riz, poulet


def test_update_stock_clamp_a_zero(db_session):
    profil, riz, _ = _setup_profil_stock(db_session, quantite_riz=100.0)
    ligne = stock_service.update_stock(db_session, profil.id, riz.id, 250.0)
    assert ligne.quantite_disponible == 0.0


def test_update_stock_404_si_absent(db_session):
    profil, _, _ = _setup_profil_stock(db_session)
    with pytest.raises(HTTPException) as exc:
        stock_service.update_stock(db_session, profil.id, "inconnu", 10.0)
    assert exc.value.status_code == 404


def test_recrediter_stock(db_session):
    profil, riz, _ = _setup_profil_stock(db_session, quantite_riz=100.0)
    stock_service.update_stock(db_session, profil.id, riz.id, 40.0)
    ligne = stock_service.recrediter_stock(db_session, profil.id, riz.id, 40.0)
    assert ligne.quantite_disponible == 100.0


def test_detecter_ruptures(db_session):
    profil, riz, poulet = _setup_profil_stock(
        db_session, quantite_riz=50.0, quantite_poulet=200.0
    )
    recette = Recette(
        nom="riz poulet",
        heure_conseillee=time(12, 0),
        kcal_total=500,
        tags=["dejeuner"],
    )
    db_session.add(recette)
    db_session.flush()
    db_session.add_all(
        [
            RecetteIngredient(
                recette_id=recette.id, ingredient_id=riz.id, poids_requis=200.0, unite="g"
            ),
            RecetteIngredient(
                recette_id=recette.id, ingredient_id=poulet.id, poids_requis=100.0, unite="g"
            ),
        ]
    )
    planning = Planning(profil_id=profil.id, periode="semaine", date_debut=date.today())
    db_session.add(planning)
    db_session.flush()
    db_session.add(
        RepasPlanifie(
            planning_id=planning.id,
            recette_id=recette.id,
            jour=date.today(),
            type_repas="dejeuner",
        )
    )
    db_session.commit()

    ruptures = stock_service.detecter_ruptures(db_session, profil.id, planning.id)
    assert len(ruptures) == 1
    assert ruptures[0].ingredient.nom == "riz"
    assert ruptures[0].quantite_manquante == 150.0


def test_check_expiry(db_session):
    profil, riz, poulet = _setup_profil_stock(db_session)
    proches = stock_service.check_expiry(db_session, profil.id, jours=7)
    noms = {ligne.ingredient.nom for ligne in proches}
    assert "riz" in noms
    assert "poulet" not in noms


def test_check_budget_lecture_seule(db_session):
    profil, _, _ = _setup_profil_stock(db_session)
    avant = budget_service.check_budget(db_session, profil.id, 20000)
    assert avant.disponible is True
    assert avant.montant_restant == 100000

    apres = budget_service.check_budget(db_session, profil.id, 20000)
    assert apres.montant_restant == 100000


def test_deduire_budget(db_session):
    profil, _, _ = _setup_profil_stock(db_session)
    budget = budget_service.deduire_budget(db_session, profil.id, 25000)
    assert budget.montant_restant == 75000
    check = budget_service.check_budget(db_session, profil.id, 80000)
    assert check.disponible is False
