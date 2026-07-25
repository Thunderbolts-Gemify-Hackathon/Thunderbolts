from datetime import date, time

from backend.models.budget import Budget
from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.planning import Planning, RepasPlanifie
from backend.models.point_de_vente import Offre, PointDeVente
from backend.models.preferences import Preferences
from backend.models.profil import Profil
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock

ORIGIN_LAT = -18.9102
ORIGIN_LON = 47.5256


def seed_router_demo(db):
    profil = Profil(
        age=28, sexe="femme", poids=60.0, taille=165.0,
        niveau_activite="leger", objectif="perte_poids",
    )
    riz = Ingredient(nom="riz", unite_defaut="g")
    db.add_all([profil, riz])
    db.flush()

    prefs = Preferences(profil_id=profil.id, tabous=[], allergies=[])
    db.add(prefs)
    db.flush()
    db.add(Budget(preferences_id=prefs.id, montant=100000, montant_restant=100000, periode="semaine"))

    stock = Stock(profil_id=profil.id, lieu_stockage="cuisine")
    db.add(stock)
    db.flush()
    db.add(IngredientStock(stock_id=stock.id, ingredient_id=riz.id, quantite_disponible=500.0, unite="g"))

    recette = Recette(nom="riz nature", heure_conseillee=time(12, 0), kcal_total=400, tags=["dejeuner"])
    db.add(recette)
    db.flush()
    db.add(RecetteIngredient(recette_id=recette.id, ingredient_id=riz.id, poids_requis=150.0, unite="g"))

    planning = Planning(profil_id=profil.id, periode="semaine", date_debut=date.today())
    db.add(planning)
    db.flush()
    repas = RepasPlanifie(
        planning_id=planning.id, recette_id=recette.id, jour=date.today(), type_repas="dejeuner"
    )
    db.add(repas)

    pdv = PointDeVente(
        nom="Score Analakely", type="grande_surface",
        latitude=-18.9110, longitude=47.5260, horaires_verifies=True,
    )
    db.add(pdv)
    db.flush()
    db.add(Offre(point_de_vente_id=pdv.id, ingredient_id=riz.id, prix=12000, derniere_mise_a_jour=date.today()))
    db.add(Itineraire(point_de_vente_id=pdv.id, distance=0.5, niveau_securite="sur", mode_deplacement="pied"))
    db.commit()
    return profil, riz, planning, repas
