from datetime import date

import pytest

from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.localisation import Localisation
from backend.models.point_de_vente import Offre, PointDeVente
from backend.services.gemma_tools import execute_tool_call
from backend.tests.factories import make_profil

ORIGIN_LAT = -18.9102
ORIGIN_LON = 47.5256


def _profil_avec_localisation(db):
    profil = make_profil(db)
    db.add(Localisation(profil_id=profil.id, latitude=ORIGIN_LAT, longitude=ORIGIN_LON))
    db.flush()
    return profil


def _seed_pdv(db):
    pdv_proche = PointDeVente(
        nom="Score Analakely", type="grande_surface", latitude=-18.9110, longitude=47.5260
    )
    pdv_loin = PointDeVente(
        nom="Super loin", type="grossiste", latitude=-19.5000, longitude=47.5000
    )
    db.add_all([pdv_proche, pdv_loin])
    db.flush()
    db.add(
        Itineraire(
            point_de_vente_id=pdv_proche.id, distance=0.5, niveau_securite="sur", mode_deplacement="pied"
        )
    )
    db.commit()
    return pdv_proche, pdv_loin


def test_find_nearest_supermarkets_retourne_les_plus_proches(db_session):
    profil = _profil_avec_localisation(db_session)
    pdv_proche, pdv_loin = _seed_pdv(db_session)

    result = execute_tool_call(db_session, profil.id, "find_nearest_supermarkets", {})

    items = result["result"]
    noms = [r["point_de_vente"]["nom"] for r in items]
    assert pdv_proche.nom in noms
    assert pdv_loin.nom not in noms  # hors du rayon par défaut


def test_find_nearest_supermarkets_sans_localisation_renvoie_erreur(db_session):
    profil = make_profil(db_session)
    result = execute_tool_call(db_session, profil.id, "find_nearest_supermarkets", {})
    assert "error" in result


def test_find_nearby_market_reste_filtre_par_ingredient(db_session):
    profil = _profil_avec_localisation(db_session)
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add(poulet)
    db_session.flush()
    pdv_proche, _ = _seed_pdv(db_session)
    db_session.add(
        Offre(
            point_de_vente_id=pdv_proche.id,
            ingredient_id=poulet.id,
            prix=5000,
            derniere_mise_a_jour=date.today(),
        )
    )
    db_session.commit()

    result = execute_tool_call(
        db_session, profil.id, "find_nearby_market", {"ingredient_nom": "poulet"}
    )
    items = result["result"]
    assert items[0]["point_de_vente"]["nom"] == pdv_proche.nom


def test_tool_inconnu_renvoie_erreur(db_session):
    profil = make_profil(db_session)
    result = execute_tool_call(db_session, profil.id, "outil_inexistant", {})
    assert "error" in result
