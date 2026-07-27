"""Boucle QA quotidienne : onboarding → stock → suggestion → valider → stock/budget."""

from datetime import date, time, timedelta

from backend.models.depense import Depense
from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock
from backend.tests.test_patch_onboarding import _creer_utilisateur, _onboarding_minimal


def test_qa_daily_loop_suggestion_valider_stock_budget(client, db_session):
    user = _creer_utilisateur(client, "qa-loop@example.com")
    headers = {"X-API-Token": user["api_token"]}
    profil_id = _onboarding_minimal(client, headers, user["id"])

    riz = db_session.query(Ingredient).filter(Ingredient.nom == "riz").first()
    if not riz:
        riz = Ingredient(nom="riz", unite_defaut="g", prix_moyen_reference=3000)
        db_session.add(riz)
        db_session.flush()
    poulet = db_session.query(Ingredient).filter(Ingredient.nom == "poulet").first()
    if not poulet:
        poulet = Ingredient(nom="poulet", unite_defaut="g", prix_moyen_reference=12000)
        db_session.add(poulet)
        db_session.flush()

    stock = db_session.query(Stock).filter(Stock.profil_id == profil_id).first()
    if not stock:
        stock = Stock(profil_id=profil_id, lieu_stockage="cuisine")
        db_session.add(stock)
        db_session.flush()

    for ing, qty in ((riz, 500.0), (poulet, 400.0)):
        existing = (
            db_session.query(IngredientStock)
            .filter(
                IngredientStock.stock_id == stock.id,
                IngredientStock.ingredient_id == ing.id,
            )
            .first()
        )
        if existing:
            existing.quantite_disponible = qty
        else:
            db_session.add(
                IngredientStock(
                    stock_id=stock.id,
                    ingredient_id=ing.id,
                    quantite_disponible=qty,
                    unite="g",
                    date_peremption=date.today() + timedelta(days=2),
                )
            )

    recette = Recette(
        nom="poulet riz qa",
        heure_conseillee=time(19, 0),
        kcal_total=600,
        tags=["diner"],
        instructions="cuire",
    )
    db_session.add(recette)
    db_session.flush()
    db_session.add_all(
        [
            RecetteIngredient(
                recette_id=recette.id, ingredient_id=riz.id, poids_requis=150.0, unite="g"
            ),
            RecetteIngredient(
                recette_id=recette.id,
                ingredient_id=poulet.id,
                poids_requis=120.0,
                unite="g",
            ),
        ]
    )
    planning = Planning(profil_id=profil_id, periode="semaine", date_debut=date.today())
    db_session.add(planning)
    db_session.flush()
    repas = RepasPlanifie(
        planning_id=planning.id,
        recette_id=recette.id,
        jour=date.today(),
        type_repas="diner",
    )
    db_session.add(repas)
    db_session.commit()

    # suggestion ce-soir
    ce = client.get(f"/ia/{profil_id}/ce-soir", headers=headers)
    assert ce.status_code == 200
    body = ce.json()
    assert body.get("recette") or body.get("message") or body.get("recette_id")

    stock_before = {
        row.ingredient_id: row.quantite_disponible
        for row in db_session.query(IngredientStock)
        .filter(IngredientStock.stock_id == stock.id)
        .all()
    }
    budget_before = client.get(f"/budget/{profil_id}/summary", headers=headers)
    assert budget_before.status_code == 200
    restant_before = budget_before.json()["montant_restant"]

    # valider repas
    val = client.post(f"/planning/{repas.id}/valider", headers=headers)
    assert val.status_code == 200
    assert val.json()["statut"] == "consomme"

    db_session.expire_all()
    stock_after = {
        row.ingredient_id: row.quantite_disponible
        for row in db_session.query(IngredientStock)
        .filter(IngredientStock.stock_id == stock.id)
        .all()
    }
    assert stock_after[riz.id] == stock_before[riz.id] - 150.0
    assert stock_after[poulet.id] == stock_before[poulet.id] - 120.0

    budget_after = client.get(f"/budget/{profil_id}/summary", headers=headers)
    assert budget_after.status_code == 200
    # dépense repas enregistrée si coût > 0
    depenses = (
        db_session.query(Depense)
        .filter(Depense.profil_id == profil_id, Depense.source == "repas")
        .all()
    )
    if depenses:
        assert budget_after.json()["montant_restant"] < restant_before
        assert any("poulet riz" in (d.label or "") for d in depenses)
