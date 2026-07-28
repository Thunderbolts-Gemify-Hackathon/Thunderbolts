"""Tests one-trip market optimization."""

from datetime import date

from backend.data.seed import seed
from backend.models.ingredient import Ingredient
from backend.models.point_de_vente import Offre, PointDeVente
from backend.services import market_trip_service


def test_optimize_one_trip_covers_with_few_stops(db_session):
    seed(db_session)
    riz = db_session.query(Ingredient).filter_by(nom="riz").one()
    tomate = db_session.query(Ingredient).filter_by(nom="tomate").one()
    # Coords Analakely-ish
    lat, lon = -18.91, 47.52
    result = market_trip_service.optimize_one_trip(
        db_session,
        [
            {"ingredient_id": riz.id, "quantite": 1000, "unite": "g"},
            {"ingredient_id": tomate.id, "quantite": 500, "unite": "g"},
        ],
        lat=lat,
        lon=lon,
        rayon_km=20,
    )
    assert result["nb_arrets"] >= 1
    assert result["cout_estime"] > 0
    covered = {
        it["ingredient_id"]
        for stop in result["stops"]
        for it in stop["items"]
    }
    assert riz.id in covered
    assert tomate.id in covered
    assert "message" in result


def test_one_trip_http(client, db_session):
    seed(db_session)
    riz = db_session.query(Ingredient).filter_by(nom="riz").one()
    r = client.post(
        "/market/one-trip",
        json={
            "lat": -18.91,
            "lon": 47.52,
            "rayon_km": 20,
            "budget": 50000,
            "items": [
                {
                    "ingredient_nom": "riz",
                    "ingredient_id": riz.id,
                    "quantite": 2000,
                    "unite": "g",
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["nb_arrets"] >= 1
    assert body["statut"] in ("ok", "sous_budget", "au_budget", "over_budget")
