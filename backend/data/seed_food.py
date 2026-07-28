from sqlalchemy.orm import Session

from backend.data.catalog import INGREDIENTS, RECETTE_INSTRUCTIONS, RECETTES
from backend.data.seed_helpers import get_or_create
from backend.models.ingredient import Ingredient
from backend.models.recette import Recette, RecetteIngredient


def _meta_ingredient(raw) -> dict:
    """Accepte l'ancien format {nom: unite} ou le catalogue enrichi."""
    if isinstance(raw, str):
        return {
            "unite_defaut": raw,
            "categorie": "autre",
            "conservation_jours": None,
            "saison": ["toute_saison"],
            "prix_moyen_reference": None,
        }
    return {
        "unite_defaut": raw["unite"],
        "categorie": raw.get("categorie", "autre"),
        "conservation_jours": raw.get("conservation_jours"),
        "saison": raw.get("saison") or ["toute_saison"],
        "prix_moyen_reference": raw.get("prix_moyen_reference"),
    }


def _appliquer_meta(ingredient: Ingredient, meta: dict) -> None:
    """Backfill / mise à jour des champs catalogue sur un ingrédient existant."""
    ingredient.unite_defaut = meta["unite_defaut"]
    ingredient.categorie = meta["categorie"]
    ingredient.conservation_jours = meta["conservation_jours"]
    ingredient.saison = meta["saison"]
    ingredient.prix_moyen_reference = meta["prix_moyen_reference"]


def seed_food(db: Session) -> dict:
    ingredients = {}
    for nom, raw in INGREDIENTS.items():
        meta = _meta_ingredient(raw)
        ingredient = get_or_create(
            db,
            Ingredient,
            {"nom": nom},
            unite_defaut=meta["unite_defaut"],
            categorie=meta["categorie"],
            conservation_jours=meta["conservation_jours"],
            saison=meta["saison"],
            prix_moyen_reference=meta["prix_moyen_reference"],
        )
        _appliquer_meta(ingredient, meta)
        ingredients[nom] = ingredient

    for nom, (heure, kcal, prot, gluc, lip, duree, tags, lignes) in RECETTES.items():
        recette = get_or_create(
            db,
            Recette,
            {"nom": nom},
            heure_conseillee=heure,
            kcal_total=kcal,
            proteines=prot,
            glucides=gluc,
            lipides=lip,
            duree_minutes=duree,
            tags=tags,
            instructions=RECETTE_INSTRUCTIONS.get(nom),
        )
        # Resync catalogue → DB (nouveaux tags / macros après expansion du seed)
        recette.heure_conseillee = heure
        recette.kcal_total = kcal
        recette.proteines = prot
        recette.glucides = gluc
        recette.lipides = lip
        recette.duree_minutes = duree
        recette.tags = tags
        if nom in RECETTE_INSTRUCTIONS:
            recette.instructions = RECETTE_INSTRUCTIONS[nom]
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
    return ingredients
