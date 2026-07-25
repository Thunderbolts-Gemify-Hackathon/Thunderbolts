from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock
from backend.schemas.composites import RuptureOut
from backend.schemas.ingredient import IngredientOut


def get_stock_profil(db: Session, profil_id: str) -> list[IngredientStock]:
    stock = (
        db.query(Stock)
        .options(joinedload(Stock.ingredients).joinedload(IngredientStock.ingredient))
        .filter(Stock.profil_id == profil_id)
        .first()
    )
    if not stock:
        return []
    return list(stock.ingredients)


def _get_ingredient_stock(
    db: Session, profil_id: str, ingredient_id: str
) -> IngredientStock:
    ligne = (
        db.query(IngredientStock)
        .join(Stock)
        .filter(Stock.profil_id == profil_id, IngredientStock.ingredient_id == ingredient_id)
        .first()
    )
    if not ligne:
        raise HTTPException(
            status_code=404,
            detail="Ingrédient introuvable dans le stock du profil",
        )
    return ligne


def update_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    quantite_a_deduire: float,
) -> IngredientStock:
    """Déduit une quantité issue de RecetteIngredient.poids_requis — jamais une estimation."""
    if quantite_a_deduire < 0:
        raise HTTPException(status_code=400, detail="quantite_a_deduire doit être >= 0")

    ligne = _get_ingredient_stock(db, profil_id, ingredient_id)
    nouvelle_qte = max(0.0, ligne.quantite_disponible - quantite_a_deduire)
    ligne.quantite_disponible = nouvelle_qte
    ligne.stock.derniere_mise_a_jour = datetime.utcnow()
    db.commit()
    db.refresh(ligne)
    return ligne


def recrediter_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    quantite: float,
) -> IngredientStock:
    """Inverse de update_stock (annulation de validation de repas — RF-12)."""
    if quantite < 0:
        raise HTTPException(status_code=400, detail="quantite doit être >= 0")

    ligne = _get_ingredient_stock(db, profil_id, ingredient_id)
    ligne.quantite_disponible = ligne.quantite_disponible + quantite
    ligne.stock.derniere_mise_a_jour = datetime.utcnow()
    db.commit()
    db.refresh(ligne)
    return ligne


def detecter_ruptures(db: Session, profil_id: str, planning_id: str) -> list[RuptureOut]:
    planning = (
        db.query(Planning)
        .options(
            joinedload(Planning.repas)
            .joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient)
        )
        .filter(Planning.id == planning_id, Planning.profil_id == profil_id)
        .first()
    )
    if not planning:
        raise HTTPException(status_code=404, detail="Planning introuvable pour ce profil")

    requis: dict[str, float] = defaultdict(float)
    ingredients_map: dict[str, Ingredient] = {}
    for repas in planning.repas:
        if repas.statut == "annule":
            continue
        for ligne in repas.recette.ingredients:
            requis[ligne.ingredient_id] += ligne.poids_requis
            ingredients_map[ligne.ingredient_id] = ligne.ingredient

    stock_dispo = {
        ligne.ingredient_id: ligne.quantite_disponible
        for ligne in get_stock_profil(db, profil_id)
    }

    ruptures: list[RuptureOut] = []
    for ingredient_id, poids_requis in requis.items():
        disponible = stock_dispo.get(ingredient_id, 0.0)
        manquant = poids_requis - disponible
        if manquant > 0:
            ingredient = ingredients_map[ingredient_id]
            ruptures.append(
                RuptureOut(
                    ingredient=IngredientOut.model_validate(ingredient),
                    quantite_manquante=round(manquant, 2),
                    marches_suggeres=[],
                )
            )
    return ruptures


def check_expiry(
    db: Session,
    profil_id: str,
    jours: int = 7,
) -> list[IngredientStock]:
    """Retourne les IngredientStock proches de la péremption (tool calling Gemma)."""
    limite = date.today() + timedelta(days=jours)
    lignes = get_stock_profil(db, profil_id)
    return [
        ligne
        for ligne in lignes
        if ligne.date_peremption is not None and ligne.date_peremption <= limite
    ]
