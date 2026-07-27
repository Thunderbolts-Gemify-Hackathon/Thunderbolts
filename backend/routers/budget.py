from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_access
from backend.models.profil import Profil
from backend.schemas.composites import CheckBudgetResponse
from backend.schemas.depense import DepenseCreate, DepenseOut
from backend.services import budget_service

router = APIRouter(prefix="/budget", tags=["budget"])


@router.get("/{profil_id}/check", response_model=CheckBudgetResponse)
def check_budget(
    profil: Profil = Depends(require_profil_access),
    cout: float = Query(..., ge=0, description="Coût estimé à vérifier"),
    db: Session = Depends(get_db),
):
    return budget_service.check_budget(db, profil.id, cout)


@router.post("/{profil_id}/depense", response_model=DepenseOut, status_code=201)
def creer_depense(
    payload: DepenseCreate,
    profil: Profil = Depends(require_profil_access),
    db: Session = Depends(get_db),
):
    return budget_service.enregistrer_depense(db, profil.id, payload)


@router.get("/{profil_id}/historique", response_model=list[DepenseOut])
def historique(
    profil: Profil = Depends(require_profil_access),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return budget_service.historique_depenses(db, profil.id, limit=limit)


@router.get("/{profil_id}/summary")
def summary(
    profil: Profil = Depends(require_profil_access),
    db: Session = Depends(get_db),
):
    return budget_service.get_budget_summary(db, profil.id)
