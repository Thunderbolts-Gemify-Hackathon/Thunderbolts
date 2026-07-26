from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.budget import Budget
from backend.models.depense import Depense
from backend.models.preferences import Preferences
from backend.schemas.composites import CheckBudgetResponse
from backend.schemas.depense import DepenseCreate, DepenseOut


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


def enregistrer_depense(
    db: Session,
    profil_id: str,
    data: DepenseCreate,
    *,
    commit: bool = True,
) -> DepenseOut:
    if data.montant <= 0:
        raise HTTPException(status_code=400, detail="montant doit être > 0")
    budget = _get_budget_profil(db, profil_id)
    budget.montant_restant = max(0.0, budget.montant_restant - data.montant)
    depense = Depense(
        profil_id=profil_id,
        montant=data.montant,
        source=data.source,
        label=data.label,
    )
    db.add(depense)
    if commit:
        db.commit()
        db.refresh(depense)
    else:
        db.flush()
    return DepenseOut.model_validate(depense)


def historique_depenses(db: Session, profil_id: str, limit: int = 50) -> list[DepenseOut]:
    rows = (
        db.query(Depense)
        .filter(Depense.profil_id == profil_id)
        .order_by(Depense.created_at.desc())
        .limit(limit)
        .all()
    )
    return [DepenseOut.model_validate(r) for r in rows]


def get_budget_summary(db: Session, profil_id: str) -> dict:
    budget = _get_budget_profil(db, profil_id)
    pct = 0.0
    if budget.montant > 0:
        pct = round(100.0 * (1.0 - budget.montant_restant / budget.montant), 1)
    return {
        "montant": budget.montant,
        "montant_restant": budget.montant_restant,
        "periode": budget.periode,
        "devise": budget.devise,
        "pourcent_consomme": max(0.0, min(100.0, pct)),
        "recentes": historique_depenses(db, profil_id, limit=5),
    }
