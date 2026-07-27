from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_utilisateur
from backend.models.utilisateur import Utilisateur
from backend.schemas.utilisateur import (
    JwtTokenOut,
    RefreshRequest,
    UtilisateurCreate,
    UtilisateurLogin,
    UtilisateurOut,
)
from backend.services import jwt_auth, utilisateur_service

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


@router.post("", response_model=UtilisateurOut, status_code=201)
def create_utilisateur(payload: UtilisateurCreate, db: Session = Depends(get_db)):
    return utilisateur_service.create_utilisateur(db, payload)


@router.post("/login", response_model=UtilisateurOut)
def login_utilisateur(payload: UtilisateurLogin, db: Session = Depends(get_db)):
    return utilisateur_service.authenticate_utilisateur(db, payload)


@router.post("/login-jwt", response_model=JwtTokenOut)
def login_jwt(payload: UtilisateurLogin, db: Session = Depends(get_db)):
    utilisateur = utilisateur_service.authenticate_utilisateur(db, payload)
    return JwtTokenOut(
        access_token=jwt_auth.create_access_token(utilisateur.id),
        refresh_token=jwt_auth.create_refresh_token(utilisateur.id),
        api_token=utilisateur.api_token,
        utilisateur=UtilisateurOut.model_validate(utilisateur),
    )


@router.post("/refresh", response_model=JwtTokenOut)
def refresh_jwt(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        data = jwt_auth.decode_token(payload.refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    utilisateur = db.get(Utilisateur, data["sub"])
    if not utilisateur:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return JwtTokenOut(
        access_token=jwt_auth.create_access_token(utilisateur.id),
        refresh_token=jwt_auth.create_refresh_token(utilisateur.id),
        api_token=utilisateur.api_token,
        utilisateur=UtilisateurOut.model_validate(utilisateur),
    )


@router.get("/{utilisateur_id}", response_model=UtilisateurOut)
def get_utilisateur(
    utilisateur_id: str,
    current: Utilisateur = Depends(get_current_utilisateur),
):
    if current.id != utilisateur_id:
        raise HTTPException(status_code=403, detail="Accès refusé à cet utilisateur")
    return current
