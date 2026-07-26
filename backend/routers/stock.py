from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_owner
from backend.models.profil import Profil
from backend.schemas.composites import StockDeductionRequest
from backend.schemas.depense import ApprovisionnementRequest, ApprovisionnementResponse
from backend.schemas.stock import (
    IngredientStockOut,
    IngredientStockUpsert,
    StockCreate,
    StockOut,
)
from backend.services import stock_alerts, stock_service
from backend.schemas.composites import RuptureOut
from backend.schemas.stock_import import StockImportTextRequest, StockImportTextResponse
from backend.services import stock_import_service

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


@router.delete("/{profil_id}/ingredients/{ingredient_id}", status_code=204)
def remove_ingredient(
    ingredient_id: str,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    stock_service.remove_ingredient_stock(db, profil.id, ingredient_id)


@router.get("/{profil_id}/detail", response_model=StockOut)
def get_stock_detail(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    stock = stock_service.get_stock_detail(db, profil.id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock introuvable pour ce profil")
    return stock


@router.post(
    "/{profil_id}/approvisionner",
    response_model=ApprovisionnementResponse,
)
def approvisionner_stock(
    payload: ApprovisionnementRequest,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    result = stock_service.approvisionner(
        db, profil.id, payload.items, label=payload.label or "Courses"
    )
    return ApprovisionnementResponse(
        stock=[IngredientStockOut.model_validate(x) for x in result["stock"]],
        depense=result["depense"],
        montant_restant=result["montant_restant"],
    )


@router.get("/{profil_id}/alertes/peremption", response_model=list[IngredientStockOut])
def alertes_peremption(
    profil: Profil = Depends(require_profil_owner),
    jours: int = 7,
    db: Session = Depends(get_db),
):
    return stock_alerts.check_expiry(db, profil.id, jours=jours)


@router.get("/{profil_id}/alertes/ruptures", response_model=list[RuptureOut])
def alertes_ruptures(
    profil: Profil = Depends(require_profil_owner),
    planning_id: str = "",
    db: Session = Depends(get_db),
):
    if not planning_id:
        raise HTTPException(status_code=422, detail="planning_id requis")
    return stock_alerts.detecter_ruptures(db, profil.id, planning_id)


@router.post(
    "/{profil_id}/import-text",
    response_model=StockImportTextResponse,
)
def import_stock_text(
    payload: StockImportTextRequest,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    """Parse des lignes type « tomate 500g » (sans OCR) + option apply."""
    return stock_import_service.import_text(
        db, profil.id, payload.text, apply=payload.apply
    )
