from datetime import date, time

import pytest
from fastapi import HTTPException

from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.services import budget_service, stock_alerts, stock_service
from backend.tests.factories import make_stock_profil


def test_update_stock_clamp_a_zero(db_session):
    profil, riz, _ = make_stock_profil(db_session, quantite_riz=100.0)
    ligne = stock_service.update_stock(db_session, profil.id, riz.id, 250.0)
    assert ligne.quantite_disponible == 0.0


def test_update_stock_404_si_absent(db_session):
    profil, _, _ = make_stock_profil(db_session)
    with pytest.raises(HTTPException) as exc:
        stock_service.update_stock(db_session, profil.id, "inconnu", 10.0)
    assert exc.value.status_code == 404


def test_recrediter_stock(db_session):
    profil, riz, _ = make_stock_profil(db_session, quantite_riz=100.0)
    stock_service.update_stock(db_session, profil.id, riz.id, 40.0)
    ligne = stock_service.recrediter_stock(db_session, profil.id, riz.id, 40.0)
    assert ligne.quantite_disponible == 100.0


def test_detecter_ruptures(db_session):
    profil, riz, poulet = make_stock_profil(db_session, quantite_riz=50.0, quantite_poulet=200.0)
    recette = Recette(nom="riz poulet", heure_conseillee=time(12, 0), kcal_total=500, tags=["dejeuner"])
    db_session.add(recette)
    db_session.flush()
    db_session.add_all(
        [
            RecetteIngredient(recette_id=recette.id, ingredient_id=riz.id, poids_requis=200.0, unite="g"),
            RecetteIngredient(recette_id=recette.id, ingredient_id=poulet.id, poids_requis=100.0, unite="g"),
        ]
    )
    planning = Planning(profil_id=profil.id, periode="semaine", date_debut=date.today())
    db_session.add(planning)
    db_session.flush()
    db_session.add(
        RepasPlanifie(planning_id=planning.id, recette_id=recette.id, jour=date.today(), type_repas="dejeuner")
    )
    db_session.commit()

    ruptures = stock_alerts.detecter_ruptures(db_session, profil.id, planning.id)
    assert len(ruptures) == 1
    assert ruptures[0].ingredient.nom == "riz"
    assert ruptures[0].quantite_manquante == 150.0


def test_check_expiry(db_session):
    profil, _, _ = make_stock_profil(db_session)
    proches = stock_alerts.check_expiry(db_session, profil.id, jours=7)
    noms = {ligne.ingredient.nom for ligne in proches}
    assert "riz" in noms
    assert "poulet" not in noms


def test_check_budget_lecture_seule(db_session):
    profil, _, _ = make_stock_profil(db_session)
    avant = budget_service.check_budget(db_session, profil.id, 20000)
    assert avant.disponible is True
    assert budget_service.check_budget(db_session, profil.id, 20000).montant_restant == 100000


def test_deduire_budget(db_session):
    profil, _, _ = make_stock_profil(db_session)
    assert budget_service.deduire_budget(db_session, profil.id, 25000).montant_restant == 75000
    assert budget_service.check_budget(db_session, profil.id, 80000).disponible is False
