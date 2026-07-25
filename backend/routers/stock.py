from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_owner
from backend.models.profil import Profil
from backend.schemas.composites import StockDeductionRequest
from backend.schemas.stock import (
    IngredientStockOut,
    IngredientStockUpsert,
    StockCreate,
    StockOut,
)
from backend.services import stock_service

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/{profil_id}", response_model=list[IngredientStockOut])
def get_stock(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return stock_service.get_stock_profil(db, profil.id)


@router.post("/{profil_id}", response_model=StockOut, status_code=201)
def create_stock(
    payload: StockCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return stock_service.create_or_replace_stock(db, profil.id, payload)


@router.post("/{profil_id}/ingredients", response_model=IngredientStockOut)
def upsert_ingredient(
    payload: IngredientStockUpsert,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return stock_service.upsert_ingredient_stock(db, profil.id, payload)


@router.post("/{profil_id}/deduire", response_model=IngredientStockOut)
def deduire_stock(
    payload: StockDeductionRequest,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return stock_service.update_stock(
        db, profil.id, payload.ingredient_id, payload.quantite
    )


@router.get("/{profil_id}/detail", response_model=StockOut)
def get_stock_detail(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    stock = stock_service.get_stock_detail(db, profil.id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock introuvable pour ce profil")
    return stock
