from datetime import date

from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.point_de_vente import Offre, PointDeVente
from backend.services.market_service import find_nearby_market, get_meilleur_compromis, haversine

ORIGIN_LAT = -18.9102
ORIGIN_LON = 47.5256


def _seed_markets(db, ingredient_id: str):
    pdvs = [
        PointDeVente(nom="Score Analakely", type="grande_surface", latitude=-18.9110, longitude=47.5260, horaires_verifies=True),
        PointDeVente(nom="Marche sombre", type="epicerie", latitude=-18.9120, longitude=47.5270, horaires_verifies=False),
        PointDeVente(nom="Epicerie 67ha", type="epicerie", latitude=-18.9130, longitude=47.5280),
        PointDeVente(nom="Super loin", type="grossiste", latitude=-19.5000, longitude=47.5000),
    ]
    db.add_all(pdvs)
    db.flush()
    today = date.today()
    prix = [15000, 8000, 10000, 5000]
    db.add_all(
        [
            Offre(point_de_vente_id=pdvs[i].id, ingredient_id=ingredient_id, prix=prix[i], derniere_mise_a_jour=today)
            for i in range(4)
        ]
    )
    db.add_all(
        [
            Itineraire(point_de_vente_id=pdvs[0].id, distance=0.5, niveau_securite="sur", mode_deplacement="pied"),
            Itineraire(point_de_vente_id=pdvs[1].id, distance=0.8, niveau_securite="a_eviter", mode_deplacement="pied"),
            Itineraire(point_de_vente_id=pdvs[2].id, distance=1.2, niveau_securite="prudence", mode_deplacement="moto"),
        ]
    )
    db.commit()


def test_haversine_meme_point():
    assert haversine(ORIGIN_LAT, ORIGIN_LON, ORIGIN_LAT, ORIGIN_LON) == 0.0


def test_find_nearby_market_tri_et_regle_securite(db_session):
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add(poulet)
    db_session.flush()
    _seed_markets(db_session, poulet.id)

    matches = find_nearby_market(db_session, poulet.id, ORIGIN_LAT, ORIGIN_LON, rayon_km=10)
    assert "Super loin" not in [m.point_de_vente.nom for m in matches]
    assert matches[0].point_de_vente.nom != "Marche sombre"
    assert matches[-1].point_de_vente.nom == "Marche sombre"
    assert matches[-1].deprioritise is True


def test_get_meilleur_compromis(db_session):
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add(poulet)
    db_session.flush()
    _seed_markets(db_session, poulet.id)
    meilleur = get_meilleur_compromis(db_session, poulet.id, ORIGIN_LAT, ORIGIN_LON)
    assert meilleur.point_de_vente.nom == "Epicerie 67ha"
