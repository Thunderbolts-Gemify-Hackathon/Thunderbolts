from backend.data.food_catalog import INGREDIENTS, RECETTES
from backend.data.market_catalog import PRIX_BASE
from backend.data.seed import seed
from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.point_de_vente import Offre, PointDeVente
from backend.models.recette import Recette, RecetteIngredient

N_ING = len(INGREDIENTS)
N_REC = len(RECETTES)
N_PRIX = len(PRIX_BASE)


def test_seed_idempotent(db_session):
    stats1 = seed(db_session)
    assert stats1["ingredients"] == N_ING
    assert stats1["recettes"] == N_REC
    assert stats1["points_de_vente"] == 8
    assert stats1["itineraires"] == 8

    n_ing = db_session.query(Ingredient).count()
    n_rec = db_session.query(Recette).count()
    n_ri = db_session.query(RecetteIngredient).count()
    n_pdv = db_session.query(PointDeVente).count()
    n_offres = db_session.query(Offre).count()
    n_it = db_session.query(Itineraire).count()

    assert n_ing == N_ING
    assert n_rec == N_REC
    assert n_ri > 0
    assert n_pdv == 8
    assert n_offres == 8 * N_PRIX
    assert n_it == 8

    seed(db_session)
    assert db_session.query(Ingredient).count() == n_ing
    assert db_session.query(Recette).count() == n_rec
    assert db_session.query(RecetteIngredient).count() == n_ri
    assert db_session.query(PointDeVente).count() == n_pdv
    assert db_session.query(Offre).count() == n_offres
    assert db_session.query(Itineraire).count() == n_it

    niveaux = {it.niveau_securite for it in db_session.query(Itineraire).all()}
    assert niveaux == {"sur", "prudence", "a_eviter"}

    riz = db_session.query(Ingredient).filter_by(nom="riz").one()
    assert riz.categorie == "féculent"
    assert riz.conservation_jours == 365
    assert riz.saison == ["toute_saison"]
    assert riz.prix_moyen_reference == 2500.0
