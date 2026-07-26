import pytest
from fastapi import HTTPException

from backend.services import courses_service, planning_service, stock_service
from backend.tests.factories import make_planning_repas, make_stock_profil


def _setup(db, qte_riz=500.0, qte_poulet=200.0):
    profil, riz, poulet = make_stock_profil(
        db, quantite_riz=qte_riz, quantite_poulet=qte_poulet, with_budget=False
    )
    planning, repas = make_planning_repas(db, profil, riz, poulet)
    return profil, riz, poulet, planning, repas


def test_get_planning(db_session):
    profil, _, _, planning, _ = _setup(db_session)
    result = planning_service.get_planning(db_session, profil.id, "semaine", planning.date_debut)
    assert result is not None
    assert result.id == planning.id
    assert len(result.repas) == 1


def test_valider_repas_deduit_stock(db_session):
    profil, riz, poulet, _, repas = _setup(db_session)
    assert planning_service.valider_repas(db_session, repas.id).statut == "consomme"
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
    assert planning_service.annuler_validation(db_session, repas.id).statut == "planifie"
    stocks = {s.ingredient_id: s.quantite_disponible for s in stock_service.get_stock_profil(db_session, profil.id)}
    assert stocks[riz.id] == 500.0
    assert stocks[poulet.id] == 200.0


def test_liste_courses_statuts(db_session):
    _, _, _, planning, _ = _setup(db_session, qte_riz=50.0, qte_poulet=200.0)
    by_nom = {item.ingredient.nom: item for item in courses_service.get_liste_courses(db_session, planning.id)}
    assert by_nom["riz"].statut == "à acheter"
    assert by_nom["poulet"].statut == "disponible"


def test_liste_courses_convertit_kg_en_g(db_session):
    """1 kg de riz en stock doit couvrir 150 g de recette (plus de faux « à acheter »)."""
    profil, riz, poulet, planning, _ = _setup(db_session, qte_riz=1.0, qte_poulet=200.0)
    from backend.models.stock import IngredientStock, Stock

    stock = db_session.query(Stock).filter(Stock.profil_id == profil.id).one()
    ligne_riz = (
        db_session.query(IngredientStock)
        .filter(IngredientStock.stock_id == stock.id, IngredientStock.ingredient_id == riz.id)
        .one()
    )
    ligne_riz.quantite_disponible = 1.0
    ligne_riz.unite = "kg"
    db_session.commit()

    by_nom = {
        item.ingredient.nom: item
        for item in courses_service.get_liste_courses(db_session, planning.id)
    }
    assert by_nom["riz"].statut == "disponible"
    assert by_nom["riz"].stock_disponible == 1000.0


def test_valider_repas_deduit_stock_en_kg(db_session):
    profil, riz, poulet, _, repas = _setup(db_session, qte_riz=1.0, qte_poulet=200.0)
    from backend.models.stock import IngredientStock, Stock

    stock = db_session.query(Stock).filter(Stock.profil_id == profil.id).one()
    ligne_riz = (
        db_session.query(IngredientStock)
        .filter(IngredientStock.stock_id == stock.id, IngredientStock.ingredient_id == riz.id)
        .one()
    )
    ligne_riz.quantite_disponible = 1.0
    ligne_riz.unite = "kg"
    db_session.commit()

    planning_service.valider_repas(db_session, repas.id)
    stocks = {
        s.ingredient_id: (s.quantite_disponible, s.unite)
        for s in stock_service.get_stock_profil(db_session, profil.id)
    }
    # 1 kg - 150 g = 0.85 kg
    assert stocks[riz.id][1] == "kg"
    assert abs(stocks[riz.id][0] - 0.85) < 1e-6
    assert stocks[poulet.id][0] == 80.0
