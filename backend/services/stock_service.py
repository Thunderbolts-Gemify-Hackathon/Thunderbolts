from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.profil import Profil
from backend.models.stock import IngredientStock, Stock
from backend.schemas.stock import IngredientStockUpsert, StockCreate


def _stock_charge(db: Session, profil_id: str) -> Stock | None:
    return (
        db.query(Stock)
        .options(joinedload(Stock.ingredients).joinedload(IngredientStock.ingredient))
        .filter(Stock.profil_id == profil_id)
        .first()
    )


def get_stock_profil(db: Session, profil_id: str) -> list[IngredientStock]:
    stock = _stock_charge(db, profil_id)
    return list(stock.ingredients) if stock else []


def get_stock_detail(db: Session, profil_id: str) -> Stock | None:
    return _stock_charge(db, profil_id)


def create_or_replace_stock(db: Session, profil_id: str, data: StockCreate) -> Stock:
    if not db.get(Profil, profil_id):
        raise HTTPException(status_code=404, detail="Profil introuvable")

    stock = db.query(Stock).filter(Stock.profil_id == profil_id).first()
    if stock:
        raise HTTPException(status_code=409, detail="Un stock existe déjà pour ce profil")

    stock = Stock(profil_id=profil_id, lieu_stockage=data.lieu_stockage)
    db.add(stock)
    db.flush()
    for ligne in data.ingredients:
        _upsert_ligne(db, stock, ligne, commit=False)
    db.commit()
    return _stock_charge(db, profil_id)


def upsert_ingredient_stock(
    db: Session, profil_id: str, data: IngredientStockUpsert
) -> IngredientStock:
    stock = db.query(Stock).filter(Stock.profil_id == profil_id).first()
    if not stock:
        stock = Stock(profil_id=profil_id, lieu_stockage="cuisine")
        db.add(stock)
        db.flush()
    return _upsert_ligne(db, stock, data, commit=True)


def _upsert_ligne(
    db: Session,
    stock: Stock,
    data: IngredientStockUpsert,
    *,
    commit: bool,
) -> IngredientStock:
    if not db.get(Ingredient, data.ingredient_id):
        raise HTTPException(status_code=404, detail="Ingrédient introuvable")

    ligne = (
        db.query(IngredientStock)
        .filter(
            IngredientStock.stock_id == stock.id,
            IngredientStock.ingredient_id == data.ingredient_id,
        )
        .first()
    )
    if ligne:
        ligne.quantite_disponible = data.quantite_disponible
        ligne.unite = data.unite
        ligne.date_peremption = data.date_peremption
    else:
        ligne = IngredientStock(
            stock_id=stock.id,
            ingredient_id=data.ingredient_id,
            quantite_disponible=data.quantite_disponible,
            unite=data.unite,
            date_peremption=data.date_peremption,
        )
        db.add(ligne)

    stock.derniere_mise_a_jour = datetime.now(timezone.utc).replace(tzinfo=None)
    if commit:
        db.commit()
        db.refresh(ligne)
    else:
        db.flush()
    return ligne


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


def remove_ingredient_stock(db: Session, profil_id: str, ingredient_id: str) -> None:
    ligne = _get_ingredient_stock(db, profil_id, ingredient_id)
    stock = ligne.stock
    db.delete(ligne)
    stock.derniere_mise_a_jour = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()


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
