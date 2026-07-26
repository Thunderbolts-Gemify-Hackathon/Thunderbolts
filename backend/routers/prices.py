from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_owner
from backend.models.profil import Profil
from backend.schemas.price import PriceIndexOut, PriceReportCreate, PriceReportOut
from backend.services import price_service

router = APIRouter(prefix="/prices", tags=["prices"])


@router.post("/{profil_id}/reports", response_model=PriceReportOut, status_code=201)
def create_report(
    payload: PriceReportCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        return price_service.create_report(db, profil.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/reports", response_model=list[PriceReportOut])
def list_reports(
    quartier: str | None = Query(default=None),
    ingredient_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return price_service.list_reports(
        db, quartier=quartier, ingredient_id=ingredient_id
    )


@router.get("/index", response_model=list[PriceIndexOut])
def price_index(
    quartier: str | None = Query(default=None),
    ingredient_id: str | None = Query(default=None),
    jour: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return price_service.get_index(
        db, quartier=quartier, ingredient_id=ingredient_id, jour=jour
    )
