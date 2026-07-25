from datetime import date

from backend.tests.router_fixtures import ORIGIN_LAT, ORIGIN_LON, seed_router_demo


def test_routers_stock_budget_market_planning(client, db_session):
    profil, riz, planning, repas = seed_router_demo(db_session)

    r = client.get(f"/stock/{profil.id}")
    assert r.status_code == 200
    assert r.json()[0]["quantite_disponible"] == 500.0

    r = client.post(f"/stock/{profil.id}/deduire", json={"ingredient_id": riz.id, "quantite": 50})
    assert r.status_code == 200
    assert r.json()["quantite_disponible"] == 450.0

    r = client.get(f"/budget/{profil.id}/check", params={"cout": 20000})
    assert r.status_code == 200
    assert r.json()["disponible"] is True

    r = client.get("/market/nearby", params={"ingredient_id": riz.id, "lat": ORIGIN_LAT, "lon": ORIGIN_LON})
    assert r.status_code == 200
    assert r.json()[0]["prix"] == 12000

    r = client.get(
        f"/planning/{profil.id}",
        params={"periode": "semaine", "date_debut": date.today().isoformat()},
    )
    assert r.status_code == 200
    assert r.json()["id"] == planning.id

    r = client.post(f"/planning/{repas.id}/valider")
    assert r.status_code == 200
    assert r.json()["statut"] == "consomme"
    assert client.get(f"/stock/{profil.id}").json()[0]["quantite_disponible"] == 300.0

    r = client.post(f"/planning/{repas.id}/annuler")
    assert r.status_code == 200
    assert r.json()["statut"] == "planifie"

    r = client.get(f"/planning/{planning.id}/courses")
    assert r.status_code == 200
    assert r.json()[0]["statut"] == "disponible"
