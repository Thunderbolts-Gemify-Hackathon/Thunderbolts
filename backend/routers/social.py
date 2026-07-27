from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_access
from backend.models.profil import Profil
from backend.models.utilisateur import Utilisateur
from backend.services import defi_service
from backend.services import jwt_auth

router = APIRouter(prefix="/social", tags=["social"])


class DefiProgressIn(BaseModel):
    increment: float = Field(default=1.0)


def _optional_utilisateur(
    db: Session = Depends(get_db),
    x_api_token: str | None = Header(None, alias="X-API-Token"),
    authorization: str | None = Header(None),
) -> Utilisateur | None:
    token = (x_api_token or "").strip()
    if not token and authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()
        try:
            payload = jwt_auth.decode_token(bearer, expected_type="access")
            return db.get(Utilisateur, payload["sub"])
        except ValueError:
            return None
    if not token:
        return None
    return db.query(Utilisateur).filter(Utilisateur.api_token == token).first()


@router.get("/defis")
def list_defis(
    profil_id: str | None = Query(None),
    db: Session = Depends(get_db),
    utilisateur: Utilisateur | None = Depends(_optional_utilisateur),
):
    """Liste les défis. Avec token + profil_id → progression incluse."""
    if profil_id and utilisateur:
        return defi_service.list_defis_with_progress(db, profil_id)
    if profil_id and not utilisateur:
        # Sans auth on renvoie la liste sans progress (compat)
        return defi_service.list_defis_with_progress(db, None)
    return defi_service.list_defis()


@router.post("/{profil_id}/defis/{defi_id}/progress")
def post_progress(
    defi_id: str,
    payload: DefiProgressIn,
    profil: Profil = Depends(require_profil_access),
    db: Session = Depends(get_db),
):
    try:
        return defi_service.increment_progress(
            db, profil.id, defi_id, increment=payload.increment
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
