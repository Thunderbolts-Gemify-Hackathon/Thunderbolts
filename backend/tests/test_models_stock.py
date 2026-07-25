from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from backend.models.ingredient import Ingredient
from backend.models.profil import Profil
from backend.models.stock import IngredientStock, Stock


def _creer_profil(db_session) -> Profil:
    profil = Profil(
        age=30,
        sexe="homme",
        poids=70.0,
        taille=175.0,
        niveau_activite="modere",
        objectif="maintien",
    )
    db_session.add(profil)
    db_session.commit()
    db_session.refresh(profil)
    return profil


def test_creer_ingredient_stock_et_lien(db_session):
    profil = _creer_profil(db_session)
    riz = Ingredient(nom="riz", unite_defaut="g")
    db_session.add(riz)
    db_session.flush()

    stock = Stock(profil_id=profil.id, lieu_stockage="cuisine")
    db_session.add(stock)
    db_session.flush()

    ligne = IngredientStock(
        stock_id=stock.id,
        ingredient_id=riz.id,
        quantite_disponible=2000.0,
        unite="g",
        date_peremption=date.today() + timedelta(days=90),
    )
    db_session.add(ligne)
    db_session.commit()

    assert stock.profil_id == profil.id
    assert len(stock.ingredients) == 1
    assert stock.ingredients[0].ingredient.nom == "riz"
    assert profil.stock.id == stock.id


def test_contrainte_unique_stock_ingredient(db_session):
    profil = _creer_profil(db_session)
    tomate = Ingredient(nom="tomate", unite_defaut="g")
    db_session.add(tomate)
    db_session.flush()

    stock = Stock(profil_id=profil.id, lieu_stockage="frigo")
    db_session.add(stock)
    db_session.flush()

    db_session.add(
        IngredientStock(
            stock_id=stock.id,
            ingredient_id=tomate.id,
            quantite_disponible=500.0,
            unite="g",
        )
    )
    db_session.commit()

    db_session.add(
        IngredientStock(
            stock_id=stock.id,
            ingredient_id=tomate.id,
            quantite_disponible=100.0,
            unite="g",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_nom_ingredient_unique(db_session):
    db_session.add(Ingredient(nom="oignon", unite_defaut="g"))
    db_session.commit()
    db_session.add(Ingredient(nom="oignon", unite_defaut="unite"))
    with pytest.raises(IntegrityError):
        db_session.commit()
