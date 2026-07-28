from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.composites import MarketMatchOut
from backend.schemas.market_panier import (
    OneTripRequest,
    OneTripResponse,
    PanierCheckRequest,
    PanierCheckResponse,
)
from backend.services import market_panier_service, market_service, market_trip_service

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/nearby", response_model=list[MarketMatchOut])
def nearby_market(
    ingredient_id: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    rayon_km: float = Query(10, gt=0),
    profil_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return market_service.find_nearby_market(
        db,
        ingredient_id=ingredient_id,
        lat=lat,
        lon=lon,
        rayon_km=rayon_km,
        profil_id=profil_id,
    )


@router.post("/panier-check", response_model=PanierCheckResponse)
def panier_check(payload: PanierCheckRequest, db: Session = Depends(get_db)):
    return market_panier_service.check_panier(
        db,
        [i.model_dump() for i in payload.items],
        payload.budget,
        quartier=payload.quartier,
        lat=payload.lat,
        lon=payload.lon,
    )


@router.post("/one-trip", response_model=OneTripResponse)
def one_trip(payload: OneTripRequest, db: Session = Depends(get_db)):
    """Couvre la liste avec le moins d'arrêts marché possible (greedy)."""
    try:
        return market_trip_service.optimize_one_trip(
            db,
            [i.model_dump() for i in payload.items],
            lat=payload.lat,
            lon=payload.lon,
            rayon_km=payload.rayon_km,
            profil_id=payload.profil_id,
            budget=payload.budget,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
