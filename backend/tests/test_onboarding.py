from datetime import date


def test_onboarding_complet(client):
    r = client.post(
        "/onboarding/profil",
        json={
            "age": 28, "sexe": "femme", "poids": 62.0, "taille": 165.0,
            "niveau_activite": "modere", "objectif": "perte_poids", "condition_sante": "aucune",
        },
    )
    assert r.status_code == 201
    profil = r.json()
    assert profil["imc"] == 22.77
    profil_id = profil["id"]

    assert client.post(
        f"/onboarding/profil/{profil_id}/foyer",
        json={"nombre_personnes": 3, "membres": [{"age_approx": 8}, {"age_approx": 55, "regime_aligne": False, "restrictions": "arachide"}]},
    ).status_code == 201

    assert client.post(
        f"/onboarding/profil/{profil_id}/preferences",
        json={"tabous": ["porc"], "allergies": ["arachide"], "severite_allergie": "severe", "regime_specifique": "sans_porc", "aliments_detestes": ["brocoli"]},
    ).status_code == 201

    assert client.post(
        f"/onboarding/profil/{profil_id}/budget", json={"montant": 150000, "periode": "semaine"}
    ).json()["montant_restant"] == 150000

    assert client.post(
        f"/onboarding/profil/{profil_id}/localisation",
        json={"latitude": -18.9102, "longitude": 47.5256, "quartier": "Analakely", "saison": "hiver_sec"},
    ).json()["quartier"] == "Analakely"

    assert client.post(
        f"/onboarding/profil/{profil_id}/etat-du-jour",
        json={"date": date.today().isoformat(), "type": "en_forme"},
    ).json()["type"] == "en_forme"

    assert client.get(f"/onboarding/profil/{profil_id}").status_code == 200
    assert client.get(f"/onboarding/profil/{profil_id}/budget").status_code == 200


def test_budget_sans_preferences_retourne_404(client):
    profil_id = client.post(
        "/onboarding/profil",
        json={"age": 30, "sexe": "homme", "poids": 75.0, "taille": 178.0, "niveau_activite": "actif", "objectif": "maintien"},
    ).json()["id"]
    r = client.post(f"/onboarding/profil/{profil_id}/budget", json={"montant": 50000, "periode": "jour"})
    assert r.status_code == 404


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
