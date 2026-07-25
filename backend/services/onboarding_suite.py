from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.budget import Budget
from backend.models.etat_du_jour import EtatDuJour
from backend.models.foyer import Foyer
from backend.models.localisation import Localisation
from backend.models.preferences import Preferences
from backend.schemas.budget import BudgetCreate, BudgetOut
from backend.schemas.etat_du_jour import EtatDuJourCreate
from backend.schemas.foyer import FoyerOut
from backend.schemas.localisation import LocalisationCreate, LocalisationOut
from backend.schemas.preferences import PreferencesOut
from backend.services import onboarding_service
from backend.services.onboarding_service import _profil_or_404


def get_profil_complet(db: Session, profil_id: str) -> dict[str, Any]:
    """Équivalent local de GET /onboarding/{id}/complet."""
    profil_out = onboarding_service.enrich_profil_out(onboarding_service.get_profil(db, profil_id))
    foyer = (
        db.query(Foyer)
        .options(joinedload(Foyer.membres))
        .filter(Foyer.profil_id == profil_id)
        .first()
    )
    preferences = db.query(Preferences).filter(Preferences.profil_id == profil_id).first()
    budget = (
        db.query(Budget).join(Preferences).filter(Preferences.profil_id == profil_id).first()
        if preferences
        else None
    )
    localisation = db.query(Localisation).filter(Localisation.profil_id == profil_id).first()

    return {
        "profil": profil_out.model_dump(),
        "foyer": FoyerOut.model_validate(foyer).model_dump() if foyer else None,
        "preferences": (
            PreferencesOut.model_validate(preferences).model_dump() if preferences else None
        ),
        "budget": BudgetOut.model_validate(budget).model_dump() if budget else None,
        "localisation": (
            LocalisationOut.model_validate(localisation).model_dump() if localisation else None
        ),
    }


def create_budget(db: Session, profil_id: str, data: BudgetCreate) -> Budget:
    preferences = db.query(Preferences).filter(Preferences.profil_id == profil_id).first()
    if not preferences:
        raise HTTPException(status_code=404, detail="Préférences introuvables: créez-les avant le budget")
    if db.query(Budget).filter(Budget.preferences_id == preferences.id).first():
        raise HTTPException(status_code=409, detail="Un budget existe déjà pour ce profil")

    budget = Budget(
        preferences_id=preferences.id,
        montant=data.montant,
        periode=data.periode,
        montant_restant=data.montant_restant if data.montant_restant is not None else data.montant,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_budget_by_profil(db: Session, profil_id: str) -> Budget:
    budget = (
        db.query(Budget).join(Preferences).filter(Preferences.profil_id == profil_id).first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Budget introuvable pour ce profil")
    return budget


def create_localisation(db: Session, profil_id: str, data: LocalisationCreate) -> Localisation:
    _profil_or_404(db, profil_id)
    if db.query(Localisation).filter(Localisation.profil_id == profil_id).first():
        raise HTTPException(status_code=409, detail="Une localisation existe déjà pour ce profil")
    localisation = Localisation(profil_id=profil_id, **data.model_dump())
    db.add(localisation)
    db.commit()
    db.refresh(localisation)
    return localisation


def create_etat_du_jour(db: Session, profil_id: str, data: EtatDuJourCreate) -> EtatDuJour:
    foyer = db.query(Foyer).filter(Foyer.profil_id == profil_id).first()
    if not foyer:
        raise HTTPException(status_code=404, detail="Foyer introuvable pour ce profil")
    existing = (
        db.query(EtatDuJour)
        .filter(EtatDuJour.foyer_id == foyer.id, EtatDuJour.date == data.date)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Un état du jour existe déjà pour cette date")
    etat = EtatDuJour(foyer_id=foyer.id, **data.model_dump())
    db.add(etat)
    db.commit()
    db.refresh(etat)
    return etat
