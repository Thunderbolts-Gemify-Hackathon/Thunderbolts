from datetime import date


def _creer_utilisateur(client, email: str = "hery@example.com") -> dict:
    r = client.post(
        "/utilisateurs",
        json={
            "nom": "Rakoto",
            "prenom": "Hery",
            "email": email,
            "date_naissance": "1998-05-12",
            "mot_de_passe": "Passw0rd!",
        },
    )
    assert r.status_code == 201
    return r.json()


def test_onboarding_complet(client):
    user = _creer_utilisateur(client)
    headers = {"X-API-Token": user["api_token"]}

    r = client.post(
        "/onboarding/profil",
        headers=headers,
        json={
            "utilisateur_id": user["id"],
            "sexe": "femme",
            "poids": 62.0,
            "taille": 165.0,
            "niveau_activite": "modere",
            "objectif": "perte_poids",
            "condition_sante": "aucune",
        },
    )
    assert r.status_code == 201
    profil = r.json()
    assert profil["utilisateur_id"] == user["id"]
    assert profil["imc"] == 22.77
    profil_id = profil["id"]

    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/foyer",
            headers=headers,
            json={
                "nombre_personnes": 3,
                "membres": [
                    {"prenom": "Mamy", "lien": "enfant", "age_approx": 8},
                    {
                        "prenom": "Neny",
                        "lien": "parent",
                        "age_approx": 55,
                        "regime_aligne": False,
                        "restrictions": "arachide",
                    },
                ],
            },
        ).status_code
        == 201
    )

    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/preferences",
            headers=headers,
            json={
                "tabous": ["porc"],
                "allergies": ["arachide"],
                "severite_allergie": "severe",
                "regime_specifique": "sans_porc",
                "aliments_aimes": ["riz", "poulet"],
                "aliments_detestes": ["brocoli"],
            },
        ).status_code
        == 201
    )

    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/budget",
            headers=headers,
            json={"montant": 150000, "periode": "semaine"},
        ).json()["devise"]
        == "Ar"
    )

    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/localisation",
            headers=headers,
            json={
                "latitude": -18.9102,
                "longitude": 47.5256,
                "quartier": "Analakely",
                "saison": "hiver_sec",
            },
        ).json()["quartier"]
        == "Analakely"
    )

    assert (
        client.post(
            f"/onboarding/profil/{profil_id}/etat-du-jour",
            headers=headers,
            json={"date": date.today().isoformat(), "type": "en_forme"},
        ).json()["type"]
        == "en_forme"
    )

    assert client.get(f"/onboarding/profil/{profil_id}", headers=headers).status_code == 200
    assert (
        client.get(f"/onboarding/profil/{profil_id}/budget", headers=headers).status_code
        == 200
    )


def test_profil_sans_compte_refuse(client):
    r = client.post(
        "/onboarding/profil",
        json={
            "sexe": "homme",
            "poids": 75.0,
            "taille": 178.0,
            "niveau_activite": "actif",
            "objectif": "maintien",
        },
    )
    assert r.status_code in (401, 422)


def test_budget_sans_preferences_retourne_404(client):
    user = _creer_utilisateur(client, email="budget@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = client.post(
        "/onboarding/profil",
        headers=headers,
        json={
            "utilisateur_id": user["id"],
            "age": 30,
            "sexe": "homme",
            "poids": 75.0,
            "taille": 178.0,
            "niveau_activite": "actif",
            "objectif": "maintien",
        },
    ).json()["id"]
    r = client.post(
        f"/onboarding/profil/{profil_id}/budget",
        headers=headers,
        json={"montant": 50000, "periode": "jour"},
    )
    assert r.status_code == 404


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
