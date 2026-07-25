from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.budget import BudgetCreate, BudgetOut
from backend.schemas.etat_du_jour import EtatDuJourCreate, EtatDuJourOut
from backend.schemas.foyer import FoyerCreate, FoyerOut
from backend.schemas.localisation import LocalisationCreate, LocalisationOut
from backend.schemas.preferences import PreferencesCreate, PreferencesOut
from backend.schemas.profil import ProfilCreate, ProfilOut
from backend.services import onboarding_service, onboarding_suite

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/profil", response_model=ProfilOut, status_code=201)
def create_profil(payload: ProfilCreate, db: Session = Depends(get_db)):
    profil = onboarding_service.create_profil(db, payload)
    return onboarding_service.enrich_profil_out(profil)


@router.get("/profil/{profil_id}", response_model=ProfilOut)
def get_profil(profil_id: str, db: Session = Depends(get_db)):
    profil = onboarding_service.get_profil(db, profil_id)
    return onboarding_service.enrich_profil_out(profil)


@router.post("/profil/{profil_id}/foyer", response_model=FoyerOut, status_code=201)
def create_foyer(profil_id: str, payload: FoyerCreate, db: Session = Depends(get_db)):
    return onboarding_service.create_foyer(db, profil_id, payload)


@router.get("/profil/{profil_id}/foyer", response_model=FoyerOut)
def get_foyer(profil_id: str, db: Session = Depends(get_db)):
    return onboarding_service.get_foyer_by_profil(db, profil_id)


@router.post("/profil/{profil_id}/preferences", response_model=PreferencesOut, status_code=201)
def create_preferences(profil_id: str, payload: PreferencesCreate, db: Session = Depends(get_db)):
    return onboarding_service.create_preferences(db, profil_id, payload)


@router.post("/profil/{profil_id}/budget", response_model=BudgetOut, status_code=201)
def create_budget(profil_id: str, payload: BudgetCreate, db: Session = Depends(get_db)):
    return onboarding_suite.create_budget(db, profil_id, payload)


@router.get("/profil/{profil_id}/budget", response_model=BudgetOut)
def get_budget(profil_id: str, db: Session = Depends(get_db)):
    return onboarding_suite.get_budget_by_profil(db, profil_id)


@router.post("/profil/{profil_id}/localisation", response_model=LocalisationOut, status_code=201)
def create_localisation(profil_id: str, payload: LocalisationCreate, db: Session = Depends(get_db)):
    return onboarding_suite.create_localisation(db, profil_id, payload)


@router.post("/profil/{profil_id}/etat-du-jour", response_model=EtatDuJourOut, status_code=201)
def create_etat_du_jour(profil_id: str, payload: EtatDuJourCreate, db: Session = Depends(get_db)):
    return onboarding_suite.create_etat_du_jour(db, profil_id, payload)
