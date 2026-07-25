from datetime import date, time

from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.planning import Planning, RepasPlanifie
from backend.models.point_de_vente import Offre, PointDeVente
from backend.models.preferences import Preferences
from backend.models.budget import Budget
from backend.models.profil import Profil
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock


ORIGIN_LAT = -18.9102
ORIGIN_LON = 47.5256


def _seed(db_session):
    profil = Profil(
        age=28,
        sexe="femme",
        poids=60.0,
        taille=165.0,
        niveau_activite="leger",
        objectif="perte_poids",
    )
    riz = Ingredient(nom="riz", unite_defaut="g")
    db_session.add_all([profil, riz])
    db_session.flush()

    prefs = Preferences(profil_id=profil.id, tabous=[], allergies=[])
    db_session.add(prefs)
    db_session.flush()
    db_session.add(
        Budget(preferences_id=prefs.id, montant=100000, montant_restant=100000, periode="semaine")
    )

    stock = Stock(profil_id=profil.id, lieu_stockage="cuisine")
    db_session.add(stock)
    db_session.flush()
    db_session.add(
        IngredientStock(
            stock_id=stock.id,
            ingredient_id=riz.id,
            quantite_disponible=500.0,
            unite="g",
        )
    )

    recette = Recette(
        nom="riz nature",
        heure_conseillee=time(12, 0),
        kcal_total=400,
        tags=["dejeuner"],
    )
    db_session.add(recette)
    db_session.flush()
    db_session.add(
        RecetteIngredient(
            recette_id=recette.id, ingredient_id=riz.id, poids_requis=150.0, unite="g"
        )
    )

    planning = Planning(profil_id=profil.id, periode="semaine", date_debut=date.today())
    db_session.add(planning)
    db_session.flush()
    repas = RepasPlanifie(
        planning_id=planning.id,
        recette_id=recette.id,
        jour=date.today(),
        type_repas="dejeuner",
    )
    db_session.add(repas)

    pdv = PointDeVente(
        nom="Score Analakely",
        type="grande_surface",
        latitude=-18.9110,
        longitude=47.5260,
        horaires_verifies=True,
    )
    db_session.add(pdv)
    db_session.flush()
    db_session.add(
        Offre(
            point_de_vente_id=pdv.id,
            ingredient_id=riz.id,
            prix=12000,
            derniere_mise_a_jour=date.today(),
        )
    )
    db_session.add(
        Itineraire(
            point_de_vente_id=pdv.id,
            distance=0.5,
            niveau_securite="sur",
            mode_deplacement="pied",
        )
    )
    db_session.commit()
    return profil, riz, planning, repas


def test_routers_stock_budget_market_planning(client, db_session):
    profil, riz, planning, repas = _seed(db_session)

    r = client.get(f"/stock/{profil.id}")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["quantite_disponible"] == 500.0

    r = client.post(
        f"/stock/{profil.id}/deduire",
        json={"ingredient_id": riz.id, "quantite": 50},
    )
    assert r.status_code == 200
    assert r.json()["quantite_disponible"] == 450.0

    r = client.get(f"/budget/{profil.id}/check", params={"cout": 20000})
    assert r.status_code == 200
    assert r.json()["disponible"] is True
    assert r.json()["montant_restant"] == 100000

    r = client.get(
        "/market/nearby",
        params={"ingredient_id": riz.id, "lat": ORIGIN_LAT, "lon": ORIGIN_LON},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["prix"] == 12000
    assert r.json()[0]["deprioritise"] is False

    r = client.get(
        f"/planning/{profil.id}",
        params={"periode": "semaine", "date_debut": date.today().isoformat()},
    )
    assert r.status_code == 200
    assert r.json()["id"] == planning.id

    r = client.post(f"/planning/{repas.id}/valider")
    assert r.status_code == 200
    assert r.json()["statut"] == "consomme"

    r = client.get(f"/stock/{profil.id}")
    assert r.json()[0]["quantite_disponible"] == 300.0  # 450 - 150

    r = client.post(f"/planning/{repas.id}/annuler")
    assert r.status_code == 200
    assert r.json()["statut"] == "planifie"

    r = client.get(f"/planning/{planning.id}/courses")
    assert r.status_code == 200
    assert r.json()[0]["statut"] == "disponible"
    assert r.json()[0]["poids_total_requis"] == 150.0
