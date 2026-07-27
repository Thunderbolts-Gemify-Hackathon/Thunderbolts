from datetime import time

from backend.models.foyer_memory import FoyerMemory
from backend.models.ingredient import Ingredient
from backend.models.preferences import Preferences
from backend.models.recette import Recette, RecetteIngredient
from backend.schemas.feedback import RepasFeedbackCreate
from backend.services import feedback_service, repas_suggestion_service
from backend.tests.factories import make_profil


def _two_equal_recettes(db, tag="diner"):
    riz = Ingredient(nom="riz-fb", unite_defaut="g")
    db.add(riz)
    db.flush()
    liked = Recette(
        nom="liked-meal",
        heure_conseillee=time(19, 0),
        kcal_total=400,
        tags=[tag],
        duree_minutes=20,
        instructions="ok",
    )
    disliked = Recette(
        nom="disliked-meal",
        heure_conseillee=time(19, 0),
        kcal_total=400,
        tags=[tag],
        duree_minutes=20,
        instructions="ok",
    )
    db.add_all([liked, disliked])
    db.flush()
    db.add_all(
        [
            RecetteIngredient(
                recette_id=liked.id, ingredient_id=riz.id, poids_requis=100, unite="g"
            ),
            RecetteIngredient(
                recette_id=disliked.id, ingredient_id=riz.id, poids_requis=100, unite="g"
            ),
        ]
    )
    db.commit()
    return liked, disliked


def test_upsert_feedback_writes_like_memory(db_session):
    profil = make_profil(db_session)
    liked, _ = _two_equal_recettes(db_session)
    feedback_service.upsert_feedback(
        db_session,
        profil.id,
        RepasFeedbackCreate(recette_id=liked.id, note=1),
    )
    mems = db_session.query(FoyerMemory).filter(FoyerMemory.profil_id == profil.id).all()
    keys = {m.cle for m in mems}
    assert f"like:{liked.id}" in keys
    assert any(k.startswith("pref_ingredient:") for k in keys)
    like_mem = next(m for m in mems if m.cle == f"like:{liked.id}")
    assert like_mem.importance >= 1.5


def test_upsert_feedback_writes_dislike_memory(db_session):
    profil = make_profil(db_session)
    _, disliked = _two_equal_recettes(db_session)
    feedback_service.upsert_feedback(
        db_session,
        profil.id,
        RepasFeedbackCreate(recette_id=disliked.id, note=-1),
    )
    keys = {
        m.cle
        for m in db_session.query(FoyerMemory).filter(FoyerMemory.profil_id == profil.id)
    }
    assert f"dislike:{disliked.id}" in keys


def test_liked_recipe_ranks_above_equal_coverage_disliked(db_session):
    profil = make_profil(db_session)
    db_session.add(
        Preferences(
            profil_id=profil.id,
            tabous=[],
            allergies=[],
            aliments_aimes=[],
            aliments_detestes=[],
        )
    )
    db_session.commit()
    liked, disliked = _two_equal_recettes(db_session, tag="diner")

    feedback_service.upsert_feedback(
        db_session, profil.id, RepasFeedbackCreate(recette_id=liked.id, note=1)
    )
    feedback_service.upsert_feedback(
        db_session, profil.id, RepasFeedbackCreate(recette_id=disliked.id, note=-1)
    )

    _, scored, _ = repas_suggestion_service._candidats_scored(
        db_session, profil.id, "diner", None, mode="stock"
    )
    ids = [r["id"] for r in scored]
    assert liked.id in ids and disliked.id in ids
    assert ids.index(liked.id) < ids.index(disliked.id)
    liked_score = next(r["_score"] for r in scored if r["id"] == liked.id)
    disliked_score = next(r["_score"] for r in scored if r["id"] == disliked.id)
    assert liked_score > disliked_score
