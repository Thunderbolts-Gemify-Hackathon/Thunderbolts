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
