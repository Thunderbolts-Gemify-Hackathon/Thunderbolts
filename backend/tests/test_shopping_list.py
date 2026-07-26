from datetime import date, time, timedelta

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock
from backend.services import shopping_list_service
from backend.tests.factories import make_profil


def _planning_semaine_quotidien(db, *, quantite_riz_stock: float):
    """1 repas/jour × 7 jours, 200 g de riz par repas → 1400 g / semaine."""
    profil = make_profil(db)
    riz = Ingredient(
        nom="riz",
        unite_defaut="g",
        categorie="féculent",
        conservation_jours=365,
        saison=["toute_saison"],
        prix_moyen_reference=2500.0,
    )
    poulet = Ingredient(
        nom="poulet",
        unite_defaut="g",
        categorie="protéine",
        conservation_jours=2,
        saison=["toute_saison"],
        prix_moyen_reference=12000.0,
    )
    db.add_all([riz, poulet])
    db.flush()

    recette = Recette(
        nom="riz poulet test",
        heure_conseillee=time(12, 0),
        kcal_total=500,
        tags=["dejeuner"],
    )
    db.add(recette)
    db.flush()
    db.add_all(
        [
            RecetteIngredient(
                recette_id=recette.id, ingredient_id=riz.id, poids_requis=200.0, unite="g"
            ),
            RecetteIngredient(
                recette_id=recette.id, ingredient_id=poulet.id, poids_requis=100.0, unite="g"
            ),
        ]
    )

    debut = date(2026, 7, 20)
    planning = Planning(profil_id=profil.id, periode="semaine", date_debut=debut)
    db.add(planning)
    db.flush()
    for i in range(7):
        db.add(
            RepasPlanifie(
                planning_id=planning.id,
                recette_id=recette.id,
                jour=debut + timedelta(days=i),
                type_repas="dejeuner",
            )
        )

    stock = Stock(profil_id=profil.id, lieu_stockage="cuisine")
    db.add(stock)
    db.flush()
    db.add(
        IngredientStock(
            stock_id=stock.id,
            ingredient_id=riz.id,
            quantite_disponible=quantite_riz_stock,
            unite="g",
            date_peremption=debut + timedelta(days=360),
        )
    )
    db.add(
        IngredientStock(
            stock_id=stock.id,
            ingredient_id=poulet.id,
            quantite_disponible=0.0,
            unite="g",
            date_peremption=debut + timedelta(days=2),
        )
    )
    db.commit()
    return profil, riz, poulet, debut


def test_mois_environ_4x_semaine(db_session):
    profil, riz, _, debut = _planning_semaine_quotidien(db_session, quantite_riz_stock=0.0)

    semaine = shopping_list_service.generer_liste_courses_periode(
        db_session, profil.id, "semaine", debut
    )
    mois = shopping_list_service.generer_liste_courses_periode(
        db_session, profil.id, "mois", debut
    )

    riz_semaine = next(i for i in semaine if i["ingredient"].id == riz.id)
    riz_mois = next(i for i in mois if i["ingredient"].id == riz.id)

    # 30 jours / 7 ≈ 4.286 → entre 4× et 5× le besoin hebdo
    ratio = riz_mois["quantite_totale_requise"] / riz_semaine["quantite_totale_requise"]
    assert 4.0 <= ratio <= 5.0
    assert riz_semaine["quantite_totale_requise"] == 1400.0
    # 4 semaines complètes (28 j) + 2 jours = 30 × 200 g
    assert riz_mois["quantite_totale_requise"] == 6000.0


def test_riz_bien_stocke_pas_a_acheter_sur_le_mois(db_session):
    # 30 jours × 200 g = 6000 g — stock initial suffisant
    profil, riz, poulet, debut = _planning_semaine_quotidien(
        db_session, quantite_riz_stock=6000.0
    )

    mois = shopping_list_service.generer_liste_courses_periode(
        db_session, profil.id, "mois", debut
    )
    by_id = {i["ingredient"].id: i for i in mois}

    assert by_id[riz.id]["statut"] == "disponible"
    assert by_id[riz.id]["quantite_a_acheter"] == 0.0
    assert by_id[riz.id]["categorie"] == "féculent"
    assert by_id[riz.id]["ingredient"].conservation_jours == 365

    # Poulet non stocké → à acheter
    assert by_id[poulet.id]["statut"] == "à acheter"
    assert by_id[poulet.id]["quantite_a_acheter"] > 0
