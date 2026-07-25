from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.budget import Budget
from backend.models.preferences import Preferences
from backend.schemas.composites import CheckBudgetResponse


def _get_budget_profil(db: Session, profil_id: str) -> Budget:
    budget = (
        db.query(Budget)
        .join(Preferences)
        .filter(Preferences.profil_id == profil_id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Budget introuvable pour ce profil")
    return budget


def check_budget(db: Session, profil_id: str, cout_estime: float) -> CheckBudgetResponse:
    if cout_estime < 0:
        raise HTTPException(status_code=400, detail="cout_estime doit être >= 0")
    budget = _get_budget_profil(db, profil_id)
    return CheckBudgetResponse(
        disponible=budget.montant_restant >= cout_estime,
        montant_restant=budget.montant_restant,
        cout_estime=cout_estime,
    )


def deduire_budget(db: Session, profil_id: str, montant: float) -> Budget:
    if montant < 0:
        raise HTTPException(status_code=400, detail="montant doit être >= 0")
    budget = _get_budget_profil(db, profil_id)
    budget.montant_restant = max(0.0, budget.montant_restant - montant)
    db.commit()
    db.refresh(budget)
    return budget
