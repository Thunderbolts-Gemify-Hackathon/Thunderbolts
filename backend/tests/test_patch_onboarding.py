def _creer_utilisateur(client, email: str = "patch@example.com") -> dict:
    r = client.post(
        "/utilisateurs",
        json={
            "nom": "Patch",
            "prenom": "Test",
            "email": email,
            "date_naissance": "1998-05-12",
            "mot_de_passe": "Passw0rd!",
        },
    )
    assert r.status_code == 201
    return r.json()


def _onboarding_minimal(client, headers, user_id: str) -> str:
    profil = client.post(
        "/onboarding/profil",
        headers=headers,
        json={
            "utilisateur_id": user_id,
            "sexe": "homme",
            "poids": 70.0,
            "taille": 175.0,
            "niveau_activite": "modere",
            "objectif": "maintien",
        },
    ).json()
    profil_id = profil["id"]
    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/foyer",
            headers=headers,
            json={"nombre_personnes": 1, "membres": []},
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/preferences",
            headers=headers,
            json={
                "tabous": [],
                "allergies": [],
                "aliments_aimes": ["riz"],
                "aliments_detestes": [],
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/budget",
            headers=headers,
            json={"montant": 100000, "periode": "semaine"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/localisation",
            headers=headers,
            json={
                "latitude": -18.91,
                "longitude": 47.52,
                "quartier": "Analakely",
                "saison": "hiver_sec",
            },
        ).status_code
        == 201
    )
    return profil_id


def test_patch_profil_prefs_budget(client):
    user = _creer_utilisateur(client)
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    r = client.patch(
        f"/onboarding/profil/{profil_id}",
        headers=headers,
        json={"poids": 72.0, "objectif": "prise_masse"},
    )
    assert r.status_code == 200
    assert r.json()["poids"] == 72.0
    assert r.json()["objectif"] == "prise_masse"
    assert r.json()["planning_invalide"] is True

    r = client.patch(
        f"/onboarding/profil/{profil_id}/preferences",
        headers=headers,
        json={"allergies": ["arachide"], "severite_allergie": "severe"},
    )
    assert r.status_code == 200
    assert r.json()["allergies"] == ["arachide"]
    assert r.json()["planning_invalide"] is True

    r = client.patch(
        f"/onboarding/profil/{profil_id}/budget",
        headers=headers,
        json={"montant": 200000},
    )
    assert r.status_code == 200
    assert r.json()["montant"] == 200000
    assert r.json()["montant_restant"] == 200000
    assert r.json()["planning_invalide"] is True

    r = client.patch(
        f"/onboarding/profil/{profil_id}/localisation",
        headers=headers,
        json={"quartier": "67ha"},
    )
    assert r.status_code == 200
    assert r.json()["quartier"] == "67ha"
