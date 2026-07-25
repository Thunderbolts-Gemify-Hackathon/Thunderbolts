from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.composites import StockDeductionRequest
from backend.schemas.stock import IngredientStockOut, IngredientStockUpsert
from backend.services import stock_service

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/{profil_id}", response_model=list[IngredientStockOut])
def get_stock(profil_id: str, db: Session = Depends(get_db)):
    return stock_service.get_stock_profil(db, profil_id)


@router.post("/{profil_id}/ingredients", response_model=IngredientStockOut, status_code=201)
def upsert_stock_line(
    profil_id: str,
    payload: IngredientStockUpsert,
    db: Session = Depends(get_db),
):
    return stock_service.upsert_stock_line(
        db,
        profil_id,
        payload.ingredient_id,
        payload.quantite_disponible,
        payload.unite,
        payload.date_peremption,
    )


@router.post("/{profil_id}/deduire", response_model=IngredientStockOut)
def deduire_stock(
    profil_id: str,
    payload: StockDeductionRequest,
    db: Session = Depends(get_db),
):
    return stock_service.update_stock(
        db, profil_id, payload.ingredient_id, payload.quantite
    )
