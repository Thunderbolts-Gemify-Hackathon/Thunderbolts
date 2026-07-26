from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.ingredient import Ingredient
from backend.schemas.ingredient import IngredientCreate
from backend.services.market_service import seed_offres_pour_ingredient


def list_ingredients(db: Session) -> list[Ingredient]:
    return db.query(Ingredient).order_by(Ingredient.nom.asc()).all()


def create_ingredient(db: Session, payload: IngredientCreate) -> Ingredient:
    nom = payload.nom.strip().lower()
    if db.query(Ingredient).filter(Ingredient.nom.ilike(nom)).first():
        raise HTTPException(status_code=409, detail=f"Produit déjà existant: {nom}")

    ingredient = Ingredient(
        nom=nom,
        unite_defaut=payload.unite_defaut,
        categorie=payload.categorie,
        conservation_jours=payload.conservation_jours,
        saison=payload.saison,
        prix_moyen_reference=payload.prix_moyen_reference,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)

    # Sans ça, ce produit est invisible sur la carte marchés (aucune Offre) —
    # même avec la bonne localisation. Voir seed_offres_pour_ingredient.
    seed_offres_pour_ingredient(db, ingredient)
    return ingredient
