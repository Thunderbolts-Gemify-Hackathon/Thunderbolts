from datetime import date

from backend.models.localisation import Localisation
from backend.tests.router_fixtures import ORIGIN_LAT, ORIGIN_LON, auth_headers, seed_router_demo


def test_routers_stock_budget_market_planning(client, db_session):
    utilisateur, profil, riz, planning, repas = seed_router_demo(db_session)
    headers = auth_headers(utilisateur)

    r = client.get(f"/stock/{profil.id}", headers=headers)
    assert r.status_code == 200
    assert r.json()[0]["quantite_disponible"] == 500.0

    r = client.post(
        f"/stock/{profil.id}/deduire",
        headers=headers,
        json={"ingredient_id": riz.id, "quantite": 50},
    )
    assert r.status_code == 200
    assert r.json()["quantite_disponible"] == 450.0

    r = client.get(f"/budget/{profil.id}/check", headers=headers, params={"cout": 20000})
    assert r.status_code == 200
    assert r.json()["disponible"] is True

    r = client.get(
        "/market/nearby",
        params={"ingredient_id": riz.id, "lat": ORIGIN_LAT, "lon": ORIGIN_LON},
    )
    assert r.status_code == 200
    assert r.json()[0]["prix"] == 12000

    r = client.get(
        f"/planning/{profil.id}",
        headers=headers,
        params={"periode": "semaine", "date_debut": date.today().isoformat()},
    )
    assert r.status_code == 200
    assert r.json()["id"] == planning.id

    r = client.post(f"/planning/{repas.id}/valider", headers=headers)
    assert r.status_code == 200
    assert r.json()["statut"] == "consomme"
    assert (
        client.get(f"/stock/{profil.id}", headers=headers).json()[0]["quantite_disponible"]
        == 300.0
    )

    r = client.post(f"/planning/{repas.id}/annuler", headers=headers)
    assert r.status_code == 200
    assert r.json()["statut"] == "planifie"

    r = client.get(f"/planning/{planning.id}/courses", headers=headers)
    assert r.status_code == 200
    assert r.json()[0]["statut"] == "disponible"


def test_stock_upsert_via_api(client, db_session):
    utilisateur, profil, riz, _, _ = seed_router_demo(db_session)
    headers = auth_headers(utilisateur)

    r = client.post(
        f"/stock/{profil.id}/ingredients",
        headers=headers,
        json={
            "ingredient_id": riz.id,
            "quantite_disponible": 800.0,
            "unite": "g",
            "date_peremption": date.today().isoformat(),
        },
    )
    assert r.status_code == 200
    assert r.json()["quantite_disponible"] == 800.0


def test_ingredient_create_via_api(client, db_session):
    utilisateur, _, _, _, _ = seed_router_demo(db_session)
    headers = auth_headers(utilisateur)

    r = client.post(
        "/ingredients",
        headers=headers,
        json={"nom": "Lait", "unite_defaut": "l", "categorie": "autre"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["nom"] == "lait"
    assert body["unite_defaut"] == "l"

    r = client.post(
        "/ingredients",
        headers=headers,
        json={"nom": "lait", "unite_defaut": "l"},
    )
    assert r.status_code == 409

    r = client.post(
        "/ingredients",
        headers=headers,
        json={"nom": "oeufs", "unite_defaut": "pas-une-unite"},
    )
    assert r.status_code == 422


def test_stock_delete_via_api(client, db_session):
    utilisateur, profil, riz, _, _ = seed_router_demo(db_session)
    headers = auth_headers(utilisateur)

    r = client.delete(f"/stock/{profil.id}/ingredients/{riz.id}", headers=headers)
    assert r.status_code == 204

    r = client.get(f"/stock/{profil.id}", headers=headers)
    assert r.json() == []

    r = client.delete(f"/stock/{profil.id}/ingredients/{riz.id}", headers=headers)
    assert r.status_code == 404


def test_directive_courses(client, db_session):
    utilisateur, profil, riz, _, _ = seed_router_demo(db_session)
    headers = auth_headers(utilisateur)
    db_session.add(
        Localisation(
            profil_id=profil.id,
            latitude=ORIGIN_LAT,
            longitude=ORIGIN_LON,
            quartier="Analakely",
        )
    )
    db_session.commit()

    r = client.post(
        f"/ia/{profil.id}/directive-courses",
        headers=headers,
        json={"ingredient_nom": "riz"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ingredient_nom"] == "riz"
    assert body["point_de_vente"] == "Score Analakely"
    assert "va a" in body["phrase"].lower() or "Score" in body["phrase"]
    assert body["prix"] == 12000
