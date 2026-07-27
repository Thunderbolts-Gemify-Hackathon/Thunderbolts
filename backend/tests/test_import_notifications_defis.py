"""Import image stock (hook text:…) + notifications preview + défis."""

import base64

from backend.models.ingredient import Ingredient
from backend.models.stock import IngredientStock, Stock
from datetime import date, timedelta

from backend.tests.test_patch_onboarding import _creer_utilisateur, _onboarding_minimal


def test_stock_import_image_text_hook(client, db_session):
    user = _creer_utilisateur(client, "import-img@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    if not db_session.query(Ingredient).filter(Ingredient.nom == "tomate").first():
        db_session.add(Ingredient(nom="tomate", unite_defaut="g", prix_moyen_reference=2000))
        db_session.commit()

    payload_text = "text:tomate 400g"
    image_b64 = base64.b64encode(payload_text.encode("utf-8")).decode("ascii")

    r = client.post(
        f"/stock/{profil_id}/import-image",
        headers=headers,
        json={"image_base64": image_b64, "apply": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["applied"] >= 1
    assert body["source"] == "image_text_hook"
    assert any(l["label"].lower().startswith("tomate") for l in body["lines"])


def test_notifications_preview(client, db_session):
    user = _creer_utilisateur(client, "notif-prev@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    riz = db_session.query(Ingredient).filter(Ingredient.nom == "riz").first()
    if not riz:
        riz = Ingredient(nom="riz", unite_defaut="g")
        db_session.add(riz)
        db_session.flush()
    stock = Stock(profil_id=profil_id, lieu_stockage="cuisine")
    db_session.add(stock)
    db_session.flush()
    db_session.add(
        IngredientStock(
            stock_id=stock.id,
            ingredient_id=riz.id,
            quantite_disponible=200,
            unite="g",
            date_peremption=date.today() + timedelta(days=1),
        )
    )
    db_session.commit()

    r = client.get(f"/notifications/{profil_id}/preview", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["profil_id"] == profil_id
    assert isinstance(body["notifications"], list)
    kinds = {n["kind"] for n in body["notifications"]}
    assert "peremption" in kinds
    peremp = next(n for n in body["notifications"] if n["kind"] == "peremption")
    assert "riz" in peremp["body"].lower() or "périm" in peremp["body"].lower() or "utiliser" in peremp["body"].lower()


def test_social_defis_progress(client, db_session):
    user = _creer_utilisateur(client, "defis@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    bare = client.get("/social/defis")
    assert bare.status_code == 200
    assert len(bare.json()) >= 1

    with_prog = client.get(
        f"/social/defis?profil_id={profil_id}",
        headers=headers,
    )
    assert with_prog.status_code == 200
    rows = with_prog.json()
    assert all("progress" in r for r in rows)

    incr = client.post(
        f"/social/{profil_id}/defis/fait-maison/progress",
        headers=headers,
        json={"increment": 2},
    )
    assert incr.status_code == 200
    assert incr.json()["valeur"] == 2
