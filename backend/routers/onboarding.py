from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_utilisateur, require_profil_owner
from backend.models.profil import Profil
from backend.models.utilisateur import Utilisateur
from backend.schemas.budget import BudgetCreate, BudgetOut
from backend.schemas.etat_du_jour import EtatDuJourCreate, EtatDuJourOut
from backend.schemas.foyer import FoyerCreate, FoyerOut
from backend.schemas.localisation import LocalisationCreate, LocalisationOut
from backend.schemas.preferences import PreferencesCreate, PreferencesOut
from backend.schemas.profil import ProfilCreate, ProfilOut
from backend.services import onboarding_service, onboarding_suite

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/profil", response_model=ProfilOut, status_code=201)
def create_profil(
    payload: ProfilCreate,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(get_current_utilisateur),
):
    if payload.utilisateur_id != utilisateur.id:
        raise HTTPException(
            status_code=403, detail="Le token ne correspond pas à utilisateur_id"
        )
    profil = onboarding_service.create_profil(db, payload)
    return onboarding_service.enrich_profil_out(profil)


@router.get("/profil/{profil_id}", response_model=ProfilOut)
def get_profil(profil: Profil = Depends(require_profil_owner)):
    return onboarding_service.enrich_profil_out(profil)


@router.post("/profil/{profil_id}/foyer", response_model=FoyerOut, status_code=201)
def create_foyer(
    payload: FoyerCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return onboarding_service.create_foyer(db, profil.id, payload)


@router.get("/profil/{profil_id}/foyer", response_model=FoyerOut)
def get_foyer(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return onboarding_service.get_foyer_by_profil(db, profil.id)


@router.post("/profil/{profil_id}/preferences", response_model=PreferencesOut, status_code=201)
def create_preferences(
    payload: PreferencesCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return onboarding_service.create_preferences(db, profil.id, payload)


@router.post("/profil/{profil_id}/budget", response_model=BudgetOut, status_code=201)
def create_budget(
    payload: BudgetCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return onboarding_suite.create_budget(db, profil.id, payload)


@router.get("/profil/{profil_id}/budget", response_model=BudgetOut)
def get_budget(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return onboarding_suite.get_budget_by_profil(db, profil.id)


@router.post("/profil/{profil_id}/localisation", response_model=LocalisationOut, status_code=201)
def create_localisation(
    payload: LocalisationCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return onboarding_suite.create_localisation(db, profil.id, payload)


@router.post("/profil/{profil_id}/etat-du-jour", response_model=EtatDuJourOut, status_code=201)
def create_etat_du_jour(
    payload: EtatDuJourCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return onboarding_suite.create_etat_du_jour(db, profil.id, payload)
