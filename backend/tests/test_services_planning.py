from datetime import date, time

import pytest
from fastapi import HTTPException

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.profil import Profil
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock
from backend.services import planning_service, stock_service


def _setup(db_session, qte_riz=500.0, qte_poulet=200.0):
    profil = Profil(
        age=28,
        sexe="femme",
        poids=60.0,
        taille=165.0,
        niveau_activite="leger",
        objectif="perte_poids",
    )
    riz = Ingredient(nom="riz", unite_defaut="g")
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add_all([profil, riz, poulet])
    db_session.flush()

    stock = Stock(profil_id=profil.id, lieu_stockage="cuisine")
    db_session.add(stock)
    db_session.flush()
    db_session.add_all(
        [
            IngredientStock(
                stock_id=stock.id,
                ingredient_id=riz.id,
                quantite_disponible=qte_riz,
                unite="g",
            ),
            IngredientStock(
                stock_id=stock.id,
                ingredient_id=poulet.id,
                quantite_disponible=qte_poulet,
                unite="g",
            ),
        ]
    )

    recette = Recette(
        nom="poulet riz",
        heure_conseillee=time(12, 0),
        kcal_total=600,
        tags=["dejeuner"],
    )
    db_session.add(recette)
    db_session.flush()
    db_session.add_all(
        [
            RecetteIngredient(
                recette_id=recette.id, ingredient_id=riz.id, poids_requis=150.0, unite="g"
            ),
            RecetteIngredient(
                recette_id=recette.id, ingredient_id=poulet.id, poids_requis=120.0, unite="g"
            ),
        ]
    )

    planning = Planning(profil_id=profil.id, periode="semaine", date_debut=date.today())
    db_session.add(planning)
    db_session.flush()
    repas = RepasPlanifie(
        planning_id=planning.id,
        recette_id=recette.id,
        jour=date.today(),
        type_repas="dejeuner",
    )
    db_session.add(repas)
    db_session.commit()
    return profil, riz, poulet, planning, repas


def test_get_planning(db_session):
    profil, _, _, planning, _ = _setup(db_session)
    result = planning_service.get_planning(
        db_session, profil.id, "semaine", planning.date_debut
    )
    assert result is not None
    assert result.id == planning.id
    assert len(result.repas) == 1


def test_valider_repas_deduit_stock(db_session):
    profil, riz, poulet, _, repas = _setup(db_session)
    result = planning_service.valider_repas(db_session, repas.id)
    assert result.statut == "consomme"

    stocks = {s.ingredient_id: s.quantite_disponible for s in stock_service.get_stock_profil(db_session, profil.id)}
    assert stocks[riz.id] == 350.0
    assert stocks[poulet.id] == 80.0


def test_valider_repas_deux_fois_interdit(db_session):
    _, _, _, _, repas = _setup(db_session)
    planning_service.valider_repas(db_session, repas.id)
    with pytest.raises(HTTPException) as exc:
        planning_service.valider_repas(db_session, repas.id)
    assert exc.value.status_code == 400


def test_annuler_validation_recredite(db_session):
    profil, riz, poulet, _, repas = _setup(db_session)
    planning_service.valider_repas(db_session, repas.id)
    result = planning_service.annuler_validation(db_session, repas.id)
    assert result.statut == "planifie"

    stocks = {s.ingredient_id: s.quantite_disponible for s in stock_service.get_stock_profil(db_session, profil.id)}
    assert stocks[riz.id] == 500.0
    assert stocks[poulet.id] == 200.0


def test_liste_courses_statuts(db_session):
    _, riz, poulet, planning, _ = _setup(db_session, qte_riz=50.0, qte_poulet=200.0)
    liste = planning_service.get_liste_courses(db_session, planning.id)
    by_nom = {item.ingredient.nom: item for item in liste}
    assert by_nom["riz"].statut == "à acheter"
    assert by_nom["riz"].poids_total_requis == 150.0
    assert by_nom["poulet"].statut == "disponible"
