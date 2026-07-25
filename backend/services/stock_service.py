from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.stock import IngredientStock, Stock


def get_stock_profil(db: Session, profil_id: str) -> list[IngredientStock]:
    stock = (
        db.query(Stock)
        .options(joinedload(Stock.ingredients).joinedload(IngredientStock.ingredient))
        .filter(Stock.profil_id == profil_id)
        .first()
    )
    return list(stock.ingredients) if stock else []


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
        raise HTTPException(status_code=404, detail="Ingrédient introuvable dans le stock du profil")
    return ligne


def _ajuster_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    delta: float,
    *,
    commit: bool = True,
    clamp_zero: bool = False,
) -> IngredientStock:
    ligne = _get_ingredient_stock(db, profil_id, ingredient_id)
    nouvelle = ligne.quantite_disponible + delta
    ligne.quantite_disponible = max(0.0, nouvelle) if clamp_zero else nouvelle
    ligne.stock.derniere_mise_a_jour = datetime.now(timezone.utc).replace(tzinfo=None)
    if commit:
        db.commit()
        db.refresh(ligne)
    else:
        db.flush()
    return ligne


def update_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    quantite_a_deduire: float,
    *,
    commit: bool = True,
) -> IngredientStock:
    if quantite_a_deduire < 0:
        raise HTTPException(status_code=400, detail="quantite_a_deduire doit être >= 0")
    return _ajuster_stock(
        db, profil_id, ingredient_id, -quantite_a_deduire, commit=commit, clamp_zero=True
    )


def recrediter_stock(
    db: Session,
    profil_id: str,
    ingredient_id: str,
    quantite: float,
    *,
    commit: bool = True,
) -> IngredientStock:
    if quantite < 0:
        raise HTTPException(status_code=400, detail="quantite doit être >= 0")
    return _ajuster_stock(db, profil_id, ingredient_id, quantite, commit=commit)
