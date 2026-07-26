from backend.models.ingredient import Ingredient
from backend.tests.test_patch_onboarding import _creer_utilisateur, _onboarding_minimal


def test_depense_et_approvisionner(client, db_session):
    user = _creer_utilisateur(client, "depense@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    ing = Ingredient(nom="tomate-test", unite_defaut="g", prix_moyen_reference=3000)
    db_session.add(ing)
    db_session.commit()

    r = client.post(
        f"/budget/{profil_id}/depense",
        headers=headers,
        json={"montant": 5000, "source": "manuel", "label": "Test"},
    )
    assert r.status_code == 201
    assert r.json()["montant"] == 5000

    summary = client.get(f"/budget/{profil_id}/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["montant_restant"] == 95000

    r = client.post(
        f"/stock/{profil_id}/approvisionner",
        headers=headers,
        json={
            "items": [
                {
                    "ingredient_id": ing.id,
                    "quantite": 500,
                    "unite": "g",
                    "prix": 2000,
                }
            ],
            "label": "Marché",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["montant_restant"] == 93000
    assert len(body["stock"]) >= 1

    alertes = client.get(f"/stock/{profil_id}/alertes/peremption", headers=headers)
    assert alertes.status_code == 200
    assert isinstance(alertes.json(), list)
