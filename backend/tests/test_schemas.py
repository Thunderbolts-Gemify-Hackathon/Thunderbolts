from datetime import date, datetime, time

import pytest
from pydantic import ValidationError

from backend.schemas.composites import (
    CheckBudgetResponse,
    MarketMatchOut,
    RuptureOut,
    StockDeductionRequest,
)
from backend.schemas.ingredient import IngredientCreate, IngredientOut
from backend.schemas.itineraire import ItineraireOut
from backend.schemas.planning import PlanningOut, RepasPlanifieOut
from backend.schemas.point_de_vente import PointDeVenteOut
from backend.schemas.recette import RecetteCreate
from backend.schemas.stock import IngredientStockOut, StockOut


def test_ingredient_create_valide_et_invalide():
    ok = IngredientCreate(nom="riz", unite_defaut="g")
    assert ok.nom == "riz"
    with pytest.raises(ValidationError):
        IngredientCreate(nom="riz", unite_defaut="tasse")


def test_from_attributes_sur_modeles_orm_like():
    class FakeStock:
        id = "s1"
        profil_id = "p1"
        lieu_stockage = "cuisine"
        derniere_mise_a_jour = datetime(2026, 7, 25, 12, 0, 0)

    out = StockOut.model_validate(FakeStock())
    assert out.lieu_stockage == "cuisine"

    class FakeIngredientStock:
        id = "is1"
        stock_id = "s1"
        ingredient_id = "i1"
        quantite_disponible = 100.0
        unite = "g"
        date_peremption = date(2026, 8, 1)

    assert IngredientStockOut.model_validate(FakeIngredientStock()).quantite_disponible == 100.0


def test_schemas_composites_tool_calling():
    req = StockDeductionRequest(ingredient_id="i1", quantite=150.0)
    assert req.quantite == 150.0

    budget = CheckBudgetResponse(
        disponible=True, montant_restant=80000.0, cout_estime=12000.0
    )
    assert budget.disponible is True

    match = MarketMatchOut(
        point_de_vente=PointDeVenteOut(
            id="pdv1",
            nom="Score Analakely",
            type="grande_surface",
            latitude=-18.91,
            longitude=47.52,
            horaires_verifies=True,
        ),
        prix=12000.0,
        itineraire=ItineraireOut(
            id="it1",
            point_de_vente_id="pdv1",
            profil_id=None,
            distance=1.5,
            niveau_securite="sur",
            mode_deplacement="pied",
        ),
        deprioritise=False,
    )
    rupture = RuptureOut(
        ingredient=IngredientOut(id="i1", nom="poulet", unite_defaut="g"),
        quantite_manquante=200.0,
        marches_suggeres=[match],
    )
    assert len(rupture.marches_suggeres) == 1
    assert rupture.marches_suggeres[0].prix == 12000.0


def test_planning_out_avec_repas():
    planning = PlanningOut(
        id="pl1",
        profil_id="p1",
        periode="semaine",
        date_debut=date(2026, 7, 20),
        repas=[
            RepasPlanifieOut(
                id="r1",
                planning_id="pl1",
                recette_id="rec1",
                jour=date(2026, 7, 21),
                type_repas="diner",
                statut="planifie",
            )
        ],
    )
    assert len(planning.repas) == 1

    recette = RecetteCreate(
        nom="romazava",
        heure_conseillee=time(19, 0),
        tags=["diner"],
    )
    assert recette.kcal_total == 0.0
