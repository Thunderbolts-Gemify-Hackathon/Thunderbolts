from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.composites import MarketMatchOut
from backend.schemas.market_panier import PanierCheckRequest, PanierCheckResponse
from backend.services import market_panier_service, market_service

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
    )
