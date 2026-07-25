from datetime import date

from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.point_de_vente import Offre, PointDeVente
from backend.models.profil import Profil


def test_point_de_vente_offre_et_itineraire(db_session):
    profil = Profil(
        age=32,
        sexe="homme",
        poids=72.0,
        taille=178.0,
        niveau_activite="actif",
        objectif="maintien",
    )
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add_all([profil, poulet])
    db_session.flush()

    pdv = PointDeVente(
        nom="Score Analakely",
        type="grande_surface",
        latitude=-18.9102,
        longitude=47.5256,
        horaires_verifies=True,
    )
    db_session.add(pdv)
    db_session.flush()

    offre = Offre(
        point_de_vente_id=pdv.id,
        ingredient_id=poulet.id,
        prix=12000.0,
        derniere_mise_a_jour=date.today(),
    )
    itineraire = Itineraire(
        point_de_vente_id=pdv.id,
        profil_id=profil.id,
        distance=1.8,
        niveau_securite="sur",
        mode_deplacement="pied",
    )
    db_session.add_all([offre, itineraire])
    db_session.commit()

    assert pdv.horaires_verifies is True
    assert len(pdv.offres) == 1
    assert pdv.offres[0].ingredient.nom == "poulet"
    assert pdv.offres[0].prix == 12000.0
    assert len(pdv.itineraires) == 1
    assert pdv.itineraires[0].niveau_securite == "sur"
    assert profil.itineraires[0].distance == 1.8


def test_itineraire_profil_nullable(db_session):
    pdv = PointDeVente(
        nom="Epicerie 67ha",
        type="epicerie",
        latitude=-18.8792,
        longitude=47.5079,
    )
    db_session.add(pdv)
    db_session.flush()

    itineraire = Itineraire(
        point_de_vente_id=pdv.id,
        profil_id=None,
        distance=0.5,
        niveau_securite="prudence",
        mode_deplacement="moto",
    )
    db_session.add(itineraire)
    db_session.commit()

    assert itineraire.profil_id is None
    assert itineraire.niveau_securite == "prudence"
