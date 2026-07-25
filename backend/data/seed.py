from __future__ import annotations

from datetime import date, time

from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db
from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.point_de_vente import Offre, PointDeVente
from backend.models.recette import Recette, RecetteIngredient

INGREDIENTS = {
    "riz": "g",
    "bredes mafana": "g",
    "poulet": "g",
    "pois du cap": "g",
    "tomate": "g",
    "oignon": "g",
    "huile": "ml",
    "sel": "g",
    "ail": "g",
    "gingembre": "g",
    "poisson": "g",
    "haricot": "g",
    "canard": "g",
    "pois chiches": "g",
    "arachide": "g",
}

RECETTES = {
    "ravitoto sy henakisoa": (
        time(12, 0), 720, 28, 55, 38, ["dejeuner"],
        [("bredes mafana", 300, "g"), ("arachide", 80, "g"), ("riz", 200, "g"), ("oignon", 50, "g"), ("huile", 20, "ml"), ("sel", 3, "g")],
    ),
    "romazava": (
        time(12, 30), 580, 32, 40, 22, ["dejeuner"],
        [("poulet", 200, "g"), ("bredes mafana", 150, "g"), ("tomate", 100, "g"), ("oignon", 60, "g"), ("gingembre", 10, "g"), ("riz", 180, "g")],
    ),
    "poisson coco riz": (
        time(19, 0), 650, 30, 60, 24, ["diner"],
        [("poisson", 220, "g"), ("riz", 200, "g"), ("tomate", 80, "g"), ("oignon", 40, "g"), ("ail", 8, "g"), ("huile", 15, "ml")],
    ),
    "poulet coco": (
        time(12, 0), 690, 35, 45, 32, ["dejeuner"],
        [("poulet", 250, "g"), ("oignon", 50, "g"), ("ail", 10, "g"), ("gingembre", 8, "g"), ("riz", 200, "g"), ("huile", 20, "ml")],
    ),
    "achard": (
        time(12, 0), 180, 4, 20, 8, ["accompagnement"],
        [("oignon", 100, "g"), ("tomate", 80, "g"), ("huile", 25, "ml"), ("sel", 4, "g"), ("gingembre", 5, "g")],
    ),
    "varenga": (
        time(19, 0), 620, 40, 35, 28, ["diner"],
        [("poulet", 280, "g"), ("oignon", 70, "g"), ("ail", 10, "g"), ("riz", 200, "g"), ("huile", 15, "ml"), ("sel", 3, "g")],
    ),
    "hen'omby ritra": (
        time(12, 0), 700, 38, 42, 30, ["dejeuner"],
        [("canard", 250, "g"), ("oignon", 60, "g"), ("ail", 10, "g"), ("gingembre", 10, "g"), ("riz", 200, "g"), ("huile", 15, "ml")],
    ),
    "voanjobory sy henakisoa": (
        time(12, 30), 640, 26, 70, 18, ["dejeuner"],
        [("pois du cap", 200, "g"), ("oignon", 50, "g"), ("tomate", 80, "g"), ("ail", 8, "g"), ("riz", 180, "g"), ("huile", 15, "ml")],
    ),
    "lasopy": (
        time(19, 0), 320, 12, 35, 10, ["diner"],
        [("haricot", 150, "g"), ("tomate", 80, "g"), ("oignon", 50, "g"), ("ail", 6, "g"), ("gingembre", 5, "g"), ("huile", 10, "ml")],
    ),
    "kitoza oeufs riz": (
        time(7, 30), 480, 22, 50, 16, ["petit_dejeuner"],
        [("poulet", 100, "g"), ("oignon", 30, "g"), ("riz", 150, "g"), ("huile", 10, "ml"), ("sel", 2, "g")],
    ),
    "salade pois chiches": (
        time(12, 0), 350, 14, 40, 12, ["dejeuner"],
        [("pois chiches", 180, "g"), ("tomate", 100, "g"), ("oignon", 40, "g"), ("huile", 20, "ml"), ("sel", 3, "g")],
    ),
    "canard aux bredes": (
        time(19, 0), 710, 36, 38, 35, ["diner"],
        [("canard", 250, "g"), ("bredes mafana", 200, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("riz", 200, "g"), ("huile", 15, "ml")],
    ),
}

POINTS_DE_VENTE = [
    ("Score Analakely", "grande_surface", -18.9102, 47.5256, True),
    ("Shoprite 67ha", "grande_surface", -18.8792, 47.5210, True),
    ("Leader Price Ankorondrano", "grande_surface", -18.8798, 47.5219, True),
    ("Marche Andravoahangy", "epicerie", -18.9005, 47.5360, False),
    ("Epicerie Analakely Centre", "epicerie", -18.9115, 47.5270, False),
    ("Grossiste Ankorondrano", "grossiste", -18.8770, 47.5200, True),
    ("Super U Ambodivona", "grande_surface", -18.9050, 47.5300, True),
    ("Marche 67ha Sud", "epicerie", -18.8820, 47.5185, False),
]

PRIX_BASE = {
    "riz": 2500, "bredes mafana": 1500, "poulet": 12000, "pois du cap": 4000,
    "tomate": 2000, "oignon": 1800, "huile": 5000, "sel": 500, "ail": 3000,
    "gingembre": 2500, "poisson": 10000, "haricot": 3500, "canard": 15000,
    "pois chiches": 4500, "arachide": 6000,
}
PRIX_MULT = [1.15, 1.25, 1.20, 0.75, 0.85, 0.70, 1.10, 0.90]

ITINERAIRES = [
    ("Score Analakely", 0.8, "sur", "pied"),
    ("Marche Andravoahangy", 2.5, "prudence", "moto"),
    ("Epicerie Analakely Centre", 1.2, "a_eviter", "pied"),
]


def _get_or_create(db: Session, model, filtre: dict, **attrs):
    obj = db.query(model).filter_by(**filtre).first()
    if obj:
        return obj
    obj = model(**filtre, **attrs)
    db.add(obj)
    db.flush()
    return obj


def seed(db: Session | None = None) -> dict[str, int]:
    own = db is None
    if own:
        init_db()
        db = SessionLocal()

    try:
        ingredients = {
            nom: _get_or_create(db, Ingredient, {"nom": nom}, unite_defaut=unite)
            for nom, unite in INGREDIENTS.items()
        }

        for nom, (heure, kcal, prot, gluc, lip, tags, lignes) in RECETTES.items():
            recette = _get_or_create(
                db,
                Recette,
                {"nom": nom},
                heure_conseillee=heure,
                kcal_total=kcal,
                proteines=prot,
                glucides=gluc,
                lipides=lip,
                tags=tags,
            )
            if not recette.ingredients:
                for ing_nom, poids, unite in lignes:
                    db.add(
                        RecetteIngredient(
                            recette_id=recette.id,
                            ingredient_id=ingredients[ing_nom].id,
                            poids_requis=poids,
                            unite=unite,
                        )
                    )

        today = date.today()
        pdvs = {}
        for idx, (nom, type_, lat, lon, horaires) in enumerate(POINTS_DE_VENTE):
            pdv = _get_or_create(
                db,
                PointDeVente,
                {"nom": nom},
                type=type_,
                latitude=lat,
                longitude=lon,
                horaires_verifies=horaires,
            )
            pdvs[nom] = pdv
            if not pdv.offres:
                mult = PRIX_MULT[idx]
                for ing_nom, base in PRIX_BASE.items():
                    db.add(
                        Offre(
                            point_de_vente_id=pdv.id,
                            ingredient_id=ingredients[ing_nom].id,
                            prix=round(base * mult),
                            derniere_mise_a_jour=today,
                        )
                    )

        for pdv_nom, distance, securite, mode in ITINERAIRES:
            pdv = pdvs[pdv_nom]
            exists = (
                db.query(Itineraire)
                .filter_by(point_de_vente_id=pdv.id, niveau_securite=securite, profil_id=None)
                .first()
            )
            if not exists:
                db.add(
                    Itineraire(
                        point_de_vente_id=pdv.id,
                        distance=distance,
                        niveau_securite=securite,
                        mode_deplacement=mode,
                    )
                )

        db.commit()
        return {
            "ingredients": len(INGREDIENTS),
            "recettes": len(RECETTES),
            "points_de_vente": len(POINTS_DE_VENTE),
            "itineraires": len(ITINERAIRES),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    print(seed())
