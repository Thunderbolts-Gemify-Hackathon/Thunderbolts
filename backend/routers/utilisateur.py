from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_utilisateur
from backend.models.utilisateur import Utilisateur
from backend.schemas.utilisateur import UtilisateurCreate, UtilisateurOut
from backend.services import utilisateur_service

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


@router.post("", response_model=UtilisateurOut, status_code=201)
def create_utilisateur(payload: UtilisateurCreate, db: Session = Depends(get_db)):
    return utilisateur_service.create_utilisateur(db, payload)


@router.get("/{utilisateur_id}", response_model=UtilisateurOut)
def get_utilisateur(
    utilisateur_id: str,
    current: Utilisateur = Depends(get_current_utilisateur),
):
    if current.id != utilisateur_id:
        raise HTTPException(status_code=403, detail="Accès refusé à cet utilisateur")
    return current
