from datetime import date

from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.point_de_vente import Offre, PointDeVente
from backend.services.market_service import (
    find_nearby_market,
    get_meilleur_compromis,
    haversine,
)


# Analakely approx
ORIGIN_LAT = -18.9102
ORIGIN_LON = 47.5256


def _seed_markets(db_session, ingredient_id: str):
    # Proche / sûr / cher
    pdv_sur = PointDeVente(
        nom="Score Analakely",
        type="grande_surface",
        latitude=-18.9110,
        longitude=47.5260,
        horaires_verifies=True,
    )
    # Proche / a_eviter / moins cher
    pdv_eviter = PointDeVente(
        nom="Marche sombre",
        type="epicerie",
        latitude=-18.9120,
        longitude=47.5270,
        horaires_verifies=False,
    )
    # Proche / prudence / prix moyen
    pdv_prudence = PointDeVente(
        nom="Epicerie 67ha",
        type="epicerie",
        latitude=-18.9130,
        longitude=47.5280,
    )
    # Hors rayon
    pdv_loin = PointDeVente(
        nom="Super loin",
        type="grossiste",
        latitude=-19.5000,
        longitude=47.5000,
    )
    db_session.add_all([pdv_sur, pdv_eviter, pdv_prudence, pdv_loin])
    db_session.flush()

    today = date.today()
    db_session.add_all(
        [
            Offre(
                point_de_vente_id=pdv_sur.id,
                ingredient_id=ingredient_id,
                prix=15000,
                derniere_mise_a_jour=today,
            ),
            Offre(
                point_de_vente_id=pdv_eviter.id,
                ingredient_id=ingredient_id,
                prix=8000,
                derniere_mise_a_jour=today,
            ),
            Offre(
                point_de_vente_id=pdv_prudence.id,
                ingredient_id=ingredient_id,
                prix=10000,
                derniere_mise_a_jour=today,
            ),
            Offre(
                point_de_vente_id=pdv_loin.id,
                ingredient_id=ingredient_id,
                prix=5000,
                derniere_mise_a_jour=today,
            ),
        ]
    )
    db_session.add_all(
        [
            Itineraire(
                point_de_vente_id=pdv_sur.id,
                distance=0.5,
                niveau_securite="sur",
                mode_deplacement="pied",
            ),
            Itineraire(
                point_de_vente_id=pdv_eviter.id,
                distance=0.8,
                niveau_securite="a_eviter",
                mode_deplacement="pied",
            ),
            Itineraire(
                point_de_vente_id=pdv_prudence.id,
                distance=1.2,
                niveau_securite="prudence",
                mode_deplacement="moto",
            ),
        ]
    )
    db_session.commit()
    return pdv_sur, pdv_eviter, pdv_prudence


def test_haversine_meme_point():
    assert haversine(ORIGIN_LAT, ORIGIN_LON, ORIGIN_LAT, ORIGIN_LON) == 0.0


def test_find_nearby_market_tri_et_regle_securite(db_session):
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add(poulet)
    db_session.flush()
    _seed_markets(db_session, poulet.id)

    matches = find_nearby_market(
        db_session, poulet.id, ORIGIN_LAT, ORIGIN_LON, rayon_km=10
    )
    noms = [m.point_de_vente.nom for m in matches]
    assert "Super loin" not in noms
    assert len(matches) == 3

    # a_eviter jamais en premier même s'il est le moins cher
    assert matches[0].point_de_vente.nom != "Marche sombre"
    assert matches[0].deprioritise is False
    assert matches[-1].point_de_vente.nom == "Marche sombre"
    assert matches[-1].deprioritise is True

    # Les non dépriorisés sont triés par prix
    non_deprio = [m for m in matches if not m.deprioritise]
    assert [m.prix for m in non_deprio] == sorted(m.prix for m in non_deprio)


def test_get_meilleur_compromis(db_session):
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add(poulet)
    db_session.flush()
    _seed_markets(db_session, poulet.id)

    meilleur = get_meilleur_compromis(db_session, poulet.id, ORIGIN_LAT, ORIGIN_LON)
    # Top 3 prix : 8000 a_eviter, 10000 prudence, 15000 sur → premier non a_eviter = prudence
    assert meilleur.point_de_vente.nom == "Epicerie 67ha"
    assert meilleur.deprioritise is False
