import uuid
from datetime import date

from backend.models.foyer import Foyer
from backend.models.localisation import Localisation
from backend.models.utilisateur import Utilisateur
from backend.tests.router_fixtures import ORIGIN_LAT, ORIGIN_LON, auth_headers, seed_router_demo


def test_mine_complet_sans_profil_renvoie_404(client, db_session):
    utilisateur = Utilisateur(
        nom="Sans",
        prenom="Profil",
        email=f"sans-profil-{uuid.uuid4().hex[:8]}@example.com",
        date_naissance=date(1990, 1, 1),
        api_token=uuid.uuid4().hex,
    )
    db_session.add(utilisateur)
    db_session.commit()

    r = client.get("/onboarding/mine/complet", headers=auth_headers(utilisateur))
    assert r.status_code == 404


def test_mine_complet_sans_token_est_refuse(client):
    r = client.get("/onboarding/mine/complet")
    assert r.status_code in (401, 422)  # header manquant (422) vs token invalide (401)


def test_mine_complet_onboarding_partiel(client, db_session):
    """Profil + préférences + budget faits, foyer et localisation pas encore —
    exactement le cas d'un onboarding interrompu en cours de route."""
    utilisateur, profil, _, _, _ = seed_router_demo(db_session)

    r = client.get("/onboarding/mine/complet", headers=auth_headers(utilisateur))
    assert r.status_code == 200
    body = r.json()
    assert body["profil"]["id"] == profil.id
    assert body["preferences"] is not None
    assert body["budget"] is not None
    assert body["foyer"] is None
    assert body["localisation"] is None


def test_mine_complet_onboarding_termine(client, db_session):
    utilisateur, profil, _, _, _ = seed_router_demo(db_session)
    db_session.add(Foyer(profil_id=profil.id, nombre_personnes=3))
    db_session.add(
        Localisation(
            profil_id=profil.id,
            latitude=ORIGIN_LAT,
            longitude=ORIGIN_LON,
            quartier="Analakely",
            saison="ete_humide",
        )
    )
    db_session.commit()

    r = client.get("/onboarding/mine/complet", headers=auth_headers(utilisateur))
    assert r.status_code == 200
    body = r.json()
    assert body["foyer"]["nombre_personnes"] == 3
    assert body["localisation"]["quartier"] == "Analakely"
    assert body["localisation"]["latitude"] == ORIGIN_LAT
