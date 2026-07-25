from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.composites import CheckBudgetResponse
from backend.services import budget_service

router = APIRouter(prefix="/budget", tags=["budget"])


@router.get("/{profil_id}/check", response_model=CheckBudgetResponse)
def check_budget(
    profil_id: str,
    cout: float = Query(..., ge=0, description="Coût estimé à vérifier"),
    db: Session = Depends(get_db),
):
    return budget_service.check_budget(db, profil_id, cout)
