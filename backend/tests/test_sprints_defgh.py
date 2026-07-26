"""Tests critiques sprints D–H + Phase 4."""

from backend.models.ingredient import Ingredient
from backend.models.recette import Recette
from backend.tests.test_patch_onboarding import _creer_utilisateur, _onboarding_minimal


def test_courses_terminer(client, db_session):
    user = _creer_utilisateur(client, "courses-terminer@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    ing = Ingredient(nom="tomate-courses", unite_defaut="g", prix_moyen_reference=2000)
    db_session.add(ing)
    db_session.commit()

    created = client.post(
        f"/planning/{profil_id}/courses/items",
        headers=headers,
        json={
            "label": "tomate-courses",
            "ingredient_id": ing.id,
            "quantite": 500,
            "unite": "g",
            "prix_estime": 1000,
            "custom": True,
        },
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    client.patch(
        f"/planning/{profil_id}/courses/items/{item_id}",
        headers=headers,
        json={"coche": True},
    )

    r = client.post(
        f"/planning/{profil_id}/courses/terminer",
        headers=headers,
        json={"item_ids": [item_id], "label": "Marché test"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["items_termines"] == 1
    assert body["stock_approvisionne"] == 1

    items = client.get(
        f"/planning/{profil_id}/courses/items",
        headers=headers,
    )
    assert items.status_code == 200
    assert items.json() == []


def test_recettes_list_and_filter(client, db_session):
    user = _creer_utilisateur(client, "recettes-list@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    # seed via onboarding may already have recettes; ensure at least one
    if db_session.query(Recette).count() == 0:
        db_session.add(
            Recette(
                nom="test salade rapide",
                kcal_total=200,
                proteines=5,
                glucides=20,
                lipides=8,
                duree_minutes=10,
                tags=["dejeuner", "rapide"],
            )
        )
        db_session.commit()

    r = client.get("/recettes")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1

    r2 = client.get("/recettes?q=romazava")
    assert r2.status_code == 200

    r3 = client.get("/recettes?tags=rapide&max_duree=20")
    assert r3.status_code == 200
    for item in r3.json():
        if item.get("duree_minutes") is not None:
            assert item["duree_minutes"] <= 20

    # user recipe
    ing = db_session.query(Ingredient).first()
    payload = {
        "nom": "Ma salade perso",
        "kcal_total": 250,
        "tags": ["dejeuner"],
        "ingredients": (
            [{"ingredient_id": ing.id, "poids_requis": 100, "unite": "g"}] if ing else []
        ),
    }
    created = client.post(f"/recettes/{profil_id}", headers=headers, json=payload)
    assert created.status_code == 201
    assert created.json()["owner_profil_id"] == profil_id

    listed = client.get(f"/recettes?profil_id={profil_id}", headers=headers)
    assert listed.status_code == 200
    assert any(x["nom"] == "Ma salade perso" for x in listed.json())


def test_agent_digest(client, db_session):
    user = _creer_utilisateur(client, "agent-digest@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    r = client.get(f"/ia/{profil_id}/agent/digest", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "resume" in body
    assert "actions" in body
    assert "alertes_stock" in body
    assert "budget" in body


def test_price_report(client, db_session):
    user = _creer_utilisateur(client, "price-report@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    ing = Ingredient(nom="oignon-prix", unite_defaut="g", prix_moyen_reference=1800)
    db_session.add(ing)
    db_session.commit()

    r = client.post(
        f"/prices/{profil_id}/reports",
        headers=headers,
        json={
            "ingredient_id": ing.id,
            "quartier": "Analakely",
            "prix": 2000,
            "unite": "kg",
        },
    )
    assert r.status_code == 201
    assert r.json()["prix"] == 2000

    idx = client.get("/prices/index?quartier=analakely")
    assert idx.status_code == 200
    data = idx.json()
    assert any(x["ingredient_id"] == ing.id for x in data)


def test_anti_gaspi(client, db_session):
    user = _creer_utilisateur(client, "anti-gaspi@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    r = client.get(f"/ia/{profil_id}/anti-gaspi", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "ariary_sauves" in body
    assert "streak_jours" in body
    assert "message" in body


def test_notification_prefs_and_favoris(client, db_session):
    user = _creer_utilisateur(client, "notif-fav@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    prefs = client.get(f"/notifications/{profil_id}/preferences", headers=headers)
    assert prefs.status_code == 200
    assert prefs.json()["enabled"] is True

    upd = client.put(
        f"/notifications/{profil_id}/preferences",
        headers=headers,
        json={"ce_soir": False, "peremption": True},
    )
    assert upd.status_code == 200
    assert upd.json()["ce_soir"] is False

    recette = db_session.query(Recette).first()
    if not recette:
        recette = Recette(
            nom="fav test",
            kcal_total=100,
            proteines=1,
            glucides=10,
            lipides=1,
            tags=["diner"],
        )
        db_session.add(recette)
        db_session.commit()

    fav = client.post(f"/favoris/{profil_id}/{recette.id}", headers=headers)
    assert fav.status_code == 200
    assert fav.json()["favori"] is True


def test_panier_check_and_social(client):
    r = client.post(
        "/market/panier-check",
        json={
            "items": [
                {"ingredient_nom": "poulet", "quantite": 500, "unite": "g"},
                {"ingredient_nom": "riz", "quantite": 1000, "unite": "g"},
            ],
            "budget": 5000,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["statut"] in ("sous_budget", "au_budget", "over_budget")
    assert "cout_estime" in body

    defis = client.get("/social/defis")
    assert defis.status_code == 200
    assert len(defis.json()) >= 1


def test_stock_import_text(client, db_session):
    user = _creer_utilisateur(client, "import-text@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    # ensure tomate exists
    if not db_session.query(Ingredient).filter(Ingredient.nom == "tomate").first():
        db_session.add(Ingredient(nom="tomate", unite_defaut="g", prix_moyen_reference=2000))
        db_session.commit()

    preview = client.post(
        f"/stock/{profil_id}/import-text",
        headers=headers,
        json={"text": "tomate 500g\noignon 200g", "apply": False},
    )
    assert preview.status_code == 200
    assert preview.json()["applied"] == 0
    assert len(preview.json()["lines"]) == 2

    applied = client.post(
        f"/stock/{profil_id}/import-text",
        headers=headers,
        json={"text": "tomate 500g", "apply": True},
    )
    assert applied.status_code == 200
    assert applied.json()["applied"] >= 1
