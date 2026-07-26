from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_owner
from backend.models.foyer import Foyer
from backend.models.profil import Profil
from backend.schemas.foyer_multi import FoyerInviteCreate, FoyerInviteOut, FoyerMembreLienOut
from backend.services import foyer_multi_service

router = APIRouter(prefix="/foyer", tags=["foyer-multi"])


@router.get("/{profil_id}/membres", response_model=list[FoyerMembreLienOut])
def list_membres(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    foyer = db.query(Foyer).filter(Foyer.profil_id == profil.id).first()
    if not foyer:
        raise HTTPException(status_code=404, detail="Foyer introuvable")
    return foyer_multi_service.list_liens(db, foyer.id)


@router.post("/{profil_id}/invite", response_model=FoyerInviteOut, status_code=201)
def invite_membre(
    payload: FoyerInviteCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        return foyer_multi_service.create_invite(db, profil.id, role=payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
