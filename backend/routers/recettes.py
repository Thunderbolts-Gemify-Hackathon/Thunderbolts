from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_utilisateur, require_profil_owner
from backend.models.profil import Profil
from backend.models.utilisateur import Utilisateur
from backend.schemas.recette import RecetteCreate, RecetteOut
from backend.services import recette_service

router = APIRouter(prefix="/recettes", tags=["recettes"])


@router.get("", response_model=list[RecetteOut])
def list_recettes(
    q: str | None = Query(default=None),
    tags: str | None = Query(default=None, description="Tags séparés par virgule"),
    max_duree: int | None = Query(default=None, gt=0),
    profil_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
):
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    effective_profil = None
    if profil_id:
        if not x_api_token:
            raise HTTPException(status_code=401, detail="Token API manquant")
        utilisateur = (
            db.query(Utilisateur)
            .filter(Utilisateur.api_token == x_api_token.strip())
            .first()
        )
        if not utilisateur:
            raise HTTPException(status_code=401, detail="Token API invalide")
        profil = db.get(Profil, profil_id)
        if not profil or profil.utilisateur_id != utilisateur.id:
            raise HTTPException(status_code=403, detail="Profil non autorisé")
        effective_profil = profil_id
    return recette_service.list_recettes(
        db, q=q, tags=tag_list, max_duree=max_duree, profil_id=effective_profil
    )


@router.get("/{recette_id}", response_model=RecetteOut)
def get_recette(recette_id: str, db: Session = Depends(get_db)):
    recette = recette_service.get_recette(db, recette_id)
    if not recette:
        raise HTTPException(status_code=404, detail="Recette introuvable")
    return recette


@router.post("/{profil_id}", response_model=RecetteOut, status_code=201)
def create_recette(
    payload: RecetteCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        return recette_service.create_user_recette(db, profil.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
