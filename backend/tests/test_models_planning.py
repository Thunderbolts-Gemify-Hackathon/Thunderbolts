from datetime import date, time, timedelta

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.profil import Profil
from backend.models.recette import Recette, RecetteIngredient


def _creer_profil(db_session) -> Profil:
    profil = Profil(
        age=28,
        sexe="femme",
        poids=60.0,
        taille=165.0,
        niveau_activite="leger",
        objectif="perte_poids",
    )
    db_session.add(profil)
    db_session.commit()
    db_session.refresh(profil)
    return profil


def test_recette_avec_ingredients(db_session):
    riz = Ingredient(nom="riz", unite_defaut="g")
    poulet = Ingredient(nom="poulet", unite_defaut="g")
    db_session.add_all([riz, poulet])
    db_session.flush()

    recette = Recette(
        nom="poulet coco riz",
        heure_conseillee=time(12, 0),
        kcal_total=650.0,
        proteines=35.0,
        glucides=70.0,
        lipides=20.0,
        tags=["dejeuner", "plat_chaud"],
    )
    db_session.add(recette)
    db_session.flush()

    db_session.add_all(
        [
            RecetteIngredient(
                recette_id=recette.id,
                ingredient_id=riz.id,
                poids_requis=150.0,
                unite="g",
            ),
            RecetteIngredient(
                recette_id=recette.id,
                ingredient_id=poulet.id,
                poids_requis=120.0,
                unite="g",
            ),
        ]
    )
    db_session.commit()

    assert len(recette.ingredients) == 2
    assert {ligne.ingredient.nom for ligne in recette.ingredients} == {"riz", "poulet"}
    assert recette.tags == ["dejeuner", "plat_chaud"]


def test_planning_avec_repas_planifie(db_session):
    profil = _creer_profil(db_session)
    recette = Recette(
        nom="romazava",
        heure_conseillee=time(19, 0),
        kcal_total=480.0,
        proteines=28.0,
        glucides=40.0,
        lipides=18.0,
        tags=["diner"],
    )
    db_session.add(recette)
    db_session.flush()

    planning = Planning(
        profil_id=profil.id,
        periode="semaine",
        date_debut=date.today(),
    )
    db_session.add(planning)
    db_session.flush()

    repas = RepasPlanifie(
        planning_id=planning.id,
        recette_id=recette.id,
        jour=date.today() + timedelta(days=1),
        type_repas="diner",
    )
    db_session.add(repas)
    db_session.commit()

    assert repas.statut == "planifie"
    assert len(planning.repas) == 1
    assert planning.repas[0].recette.nom == "romazava"
    assert len(profil.plannings) == 1
