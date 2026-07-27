"""Accès stock/budget partagés après acceptation d'une invitation foyer."""

from backend.models.ingredient import Ingredient
from backend.tests.test_patch_onboarding import _creer_utilisateur, _onboarding_minimal


def test_guest_can_get_post_shared_stock_and_budget(client, db_session):
    owner = _creer_utilisateur(client, "owner-share@example.com")
    owner_headers = {"X-API-Token": owner["api_token"]}
    profil_id = _onboarding_minimal(client, owner_headers, owner["id"])

    invite = client.post(
        f"/foyer/{profil_id}/invite",
        headers=owner_headers,
        json={"role": "membre"},
    )
    assert invite.status_code == 201
    token = invite.json()["invite_url"].rsplit("/", 1)[-1]

    guest = _creer_utilisateur(client, "guest-share@example.com")
    guest_headers = {"X-API-Token": guest["api_token"]}
    accepted = client.post(
        f"/foyer/invite/{token}/accept",
        headers=guest_headers,
    )
    assert accepted.status_code == 200
    assert accepted.json()["role"] == "membre"

    mine = client.get("/foyer/mine", headers=guest_headers)
    assert mine.status_code == 200
    foyers = mine.json()
    assert any(f["profil_id"] == profil_id and f["role"] == "membre" for f in foyers)

    stock_get = client.get(f"/stock/{profil_id}", headers=guest_headers)
    assert stock_get.status_code == 200

    ing = db_session.query(Ingredient).filter(Ingredient.nom == "riz").first()
    if not ing:
        ing = Ingredient(nom="riz", unite_defaut="g", prix_moyen_reference=3000)
        db_session.add(ing)
        db_session.commit()

    stock_post = client.post(
        f"/stock/{profil_id}/ingredients",
        headers=guest_headers,
        json={
            "ingredient_id": ing.id,
            "quantite_disponible": 250,
            "unite": "g",
        },
    )
    assert stock_post.status_code == 200
    assert stock_post.json()["quantite_disponible"] == 250

    budget_get = client.get(f"/budget/{profil_id}/summary", headers=guest_headers)
    assert budget_get.status_code == 200
    assert "montant_restant" in budget_get.json() or "montant" in budget_get.json()

    depense = client.post(
        f"/budget/{profil_id}/depense",
        headers=guest_headers,
        json={"montant": 1000, "source": "courses", "label": "test coloc"},
    )
    assert depense.status_code == 201
    assert depense.json()["montant"] == 1000


def test_stranger_cannot_access_stock(client):
    owner = _creer_utilisateur(client, "owner-private@example.com")
    owner_headers = {"X-API-Token": owner["api_token"]}
    profil_id = _onboarding_minimal(client, owner_headers, owner["id"])

    stranger = _creer_utilisateur(client, "stranger@example.com")
    stranger_headers = {"X-API-Token": stranger["api_token"]}
    r = client.get(f"/stock/{profil_id}", headers=stranger_headers)
    assert r.status_code == 403
