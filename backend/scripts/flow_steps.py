from datetime import date

import httpx


async def create_utilisateur(client: httpx.AsyncClient) -> dict:
    r = await client.post(
        "/utilisateurs",
        json={
            "nom": "Rakoto",
            "prenom": "Hery",
            "email": f"hery-demo-{date.today().isoformat()}@example.com",
            "date_naissance": "1998-05-12",
        },
    )
    r.raise_for_status()
    return r.json()


async def complete_onboarding(client: httpx.AsyncClient) -> tuple[str, dict[str, str]]:
    user = await create_utilisateur(client)
    headers = {"X-API-Token": user["api_token"]}

    r = await client.post(
        "/onboarding/profil",
        headers=headers,
        json={
            "utilisateur_id": user["id"],
            "age": 27,
            "sexe": "homme",
            "poids": 72.0,
            "taille": 175.0,
            "niveau_activite": "modere",
            "objectif": "maintien",
        },
    )
    r.raise_for_status()
    profil_id = r.json()["id"]

    for path, body in [
        (
            f"/onboarding/profil/{profil_id}/foyer",
            {
                "nombre_personnes": 2,
                "membres": [{"prenom": "Voahirana", "lien": "conjoint", "age_approx": 25}],
            },
        ),
        (
            f"/onboarding/profil/{profil_id}/preferences",
            {
                "tabous": ["porc"],
                "allergies": [],
                "aliments_aimes": ["riz", "poulet"],
                "aliments_detestes": [],
                "regime_specifique": "sans_porc",
            },
        ),
        (
            f"/onboarding/profil/{profil_id}/budget",
            {"montant": 200000, "periode": "semaine", "devise": "Ar"},
        ),
        (
            f"/onboarding/profil/{profil_id}/localisation",
            {
                "latitude": -18.9102,
                "longitude": 47.5256,
                "quartier": "Analakely",
                "saison": "hiver_sec",
            },
        ),
    ]:
        r = await client.post(path, headers=headers, json=body)
        r.raise_for_status()
    return profil_id, headers


async def assert_market_rules(client: httpx.AsyncClient, bredes_id: str) -> dict:
    r = await client.get(
        "/market/nearby",
        params={
            "ingredient_id": bredes_id,
            "lat": -18.9102,
            "lon": 47.5256,
            "rayon_km": 15,
        },
    )
    r.raise_for_status()
    matches = r.json()
    assert matches
    for m in matches:
        if m.get("itineraire") and m["itineraire"]["niveau_securite"] == "a_eviter":
            assert m["deprioritise"] is True
    normal = [m for m in matches if not m["deprioritise"]]
    assert [m["prix"] for m in normal] == sorted(m["prix"] for m in normal)
    return {
        "nom": matches[0]["point_de_vente"]["nom"],
        "prix": matches[0]["prix"],
        "deprioritise": matches[0]["deprioritise"],
    }


async def assert_planning_empty(
    client: httpx.AsyncClient, profil_id: str, headers: dict[str, str]
) -> None:
    r = await client.get(
        f"/planning/{profil_id}",
        headers=headers,
        params={"periode": "semaine", "date_debut": date.today().isoformat()},
    )
    assert r.status_code == 404
