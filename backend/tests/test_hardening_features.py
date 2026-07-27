from backend.tests.test_patch_onboarding import _creer_utilisateur, _onboarding_minimal


def test_foyer_invite_accept_and_feedback(client, db_session):
    from backend.models.ingredient import Ingredient
    from backend.models.recette import Recette

    owner = _creer_utilisateur(client, "owner@example.com")
    owner_headers = {"X-API-Token": owner["api_token"]}
    profil_id = _onboarding_minimal(client, owner_headers, owner["id"])

    invite = client.post(
        f"/foyer/{profil_id}/invite",
        headers=owner_headers,
        json={"role": "membre"},
    )
    assert invite.status_code == 201
    invite_url = invite.json()["invite_url"]
    token = invite_url.rsplit("/", 1)[-1]

    guest = _creer_utilisateur(client, "guest@example.com")
    guest_headers = {"X-API-Token": guest["api_token"]}
    accepted = client.post(
        f"/foyer/invite/{token}/accept",
        headers=guest_headers,
    )
    assert accepted.status_code == 200
    assert accepted.json()["utilisateur_id"] == guest["id"]
    assert accepted.json()["role"] == "membre"

    membres = client.get(f"/foyer/{profil_id}/membres", headers=owner_headers)
    assert membres.status_code == 200
    assert any(m["utilisateur_id"] == guest["id"] for m in membres.json())

    # feedback + anti-gaspi endpoints
    rec = Recette(
        nom="test-feedback",
        heure_conseillee=None,
        kcal_total=100,
        proteines=1,
        glucides=1,
        lipides=1,
        duree_minutes=10,
        tags=["diner"],
        instructions="cuire",
    )
    db_session.add(rec)
    db_session.commit()

    fb = client.post(
        f"/ia/{profil_id}/feedback",
        headers=owner_headers,
        json={"recette_id": rec.id, "note": 1},
    )
    assert fb.status_code == 201

    ag = client.get(f"/ia/{profil_id}/anti-gaspi", headers=owner_headers)
    assert ag.status_code == 200
    assert "ariary_sauves" in ag.json()

    # price report
    ing = Ingredient(nom="carotte-test", unite_defaut="g", prix_moyen_reference=2000)
    db_session.add(ing)
    db_session.commit()
    pr = client.post(
        f"/prices/{profil_id}/reports",
        headers=owner_headers,
        json={
            "ingredient_id": ing.id,
            "quartier": "Analakely",
            "prix": 2500,
            "unite": "kg",
        },
    )
    assert pr.status_code == 201

    # stock import
    imp = client.post(
        f"/stock/{profil_id}/import-text",
        headers=owner_headers,
        json={"text": "carotte-test 300g", "apply": True},
    )
    assert imp.status_code == 200
    assert imp.json()["applied"] >= 1
