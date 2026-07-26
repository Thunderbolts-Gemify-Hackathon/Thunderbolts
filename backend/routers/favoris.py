from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_owner
from backend.models.profil import Profil
from backend.schemas.favori import FavoriRecetteOut, FavoriToggleOut
from backend.services import favori_service

router = APIRouter(prefix="/favoris", tags=["favoris"])


@router.get("/{profil_id}", response_model=list[FavoriRecetteOut])
def list_favoris(
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return favori_service.list_favoris(db, profil.id)


@router.post("/{profil_id}/{recette_id}", response_model=FavoriToggleOut)
def toggle_favori(
    recette_id: str,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        return favori_service.toggle_favori(db, profil.id, recette_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{profil_id}/{recette_id}", response_model=FavoriToggleOut)
def get_favori(
    recette_id: str,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return {
        "favori": favori_service.is_favori(db, profil.id, recette_id),
        "recette_id": recette_id,
    }
