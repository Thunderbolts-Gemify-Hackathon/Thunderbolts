"""Dépendances FastAPI : auth par X-API-Token ou Authorization Bearer JWT."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.foyer import Foyer
from backend.models.foyer_membre_lien import FoyerMembreLien
from backend.models.planning import Planning, RepasPlanifie
from backend.models.profil import Profil
from backend.models.utilisateur import Utilisateur
from backend.services import jwt_auth


def _utilisateur_from_api_token(db: Session, token: str) -> Utilisateur | None:
    if not token.strip():
        return None
    return db.query(Utilisateur).filter(Utilisateur.api_token == token.strip()).first()


def _utilisateur_from_bearer(db: Session, authorization: str | None) -> Utilisateur | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    raw = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt_auth.decode_token(raw, expected_type="access")
    except ValueError:
        return None
    return db.get(Utilisateur, payload["sub"])


def get_current_utilisateur(
    db: Session = Depends(get_db),
    x_api_token: str | None = Header(None, alias="X-API-Token"),
    authorization: str | None = Header(None),
) -> Utilisateur:
    utilisateur = None
    if x_api_token:
        utilisateur = _utilisateur_from_api_token(db, x_api_token)
    if not utilisateur:
        utilisateur = _utilisateur_from_bearer(db, authorization)
    if not utilisateur:
        raise HTTPException(status_code=401, detail="Token API manquant ou invalide")
    return utilisateur


def _utilisateur_accede_profil(db: Session, utilisateur: Utilisateur, profil: Profil) -> bool:
    if profil.utilisateur_id == utilisateur.id:
        return True
    foyer = db.query(Foyer).filter(Foyer.profil_id == profil.id).first()
    if not foyer:
        return False
    lien = (
        db.query(FoyerMembreLien)
        .filter(
            FoyerMembreLien.foyer_id == foyer.id,
            FoyerMembreLien.utilisateur_id == utilisateur.id,
        )
        .first()
    )
    return lien is not None and lien.role in ("owner", "membre")


def require_profil_owner(
    profil_id: str,
    utilisateur: Utilisateur = Depends(get_current_utilisateur),
    db: Session = Depends(get_db),
) -> Profil:
    profil = db.get(Profil, profil_id)
    if not profil:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    if profil.utilisateur_id != utilisateur.id:
        raise HTTPException(status_code=403, detail="Accès refusé à ce profil")
    return profil


def require_profil_access(
    profil_id: str,
    utilisateur: Utilisateur = Depends(get_current_utilisateur),
    db: Session = Depends(get_db),
) -> Profil:
    """Propriétaire du profil OU membre du foyer (stock/budget partagés)."""
    profil = db.get(Profil, profil_id)
    if not profil:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    if not _utilisateur_accede_profil(db, utilisateur, profil):
        raise HTTPException(status_code=403, detail="Accès refusé à ce profil")
    return profil


def require_repas_owner(
    repas_id: str,
    utilisateur: Utilisateur = Depends(get_current_utilisateur),
    db: Session = Depends(get_db),
) -> RepasPlanifie:
    repas = (
        db.query(RepasPlanifie)
        .options(joinedload(RepasPlanifie.planning).joinedload(Planning.profil))
        .filter(RepasPlanifie.id == repas_id)
        .first()
    )
    if not repas:
        raise HTTPException(status_code=404, detail="Repas planifié introuvable")
    if not _utilisateur_accede_profil(db, utilisateur, repas.planning.profil):
        raise HTTPException(status_code=403, detail="Accès refusé à ce repas")
    return repas


def require_planning_owner(
    planning_id: str,
    utilisateur: Utilisateur = Depends(get_current_utilisateur),
    db: Session = Depends(get_db),
) -> Planning:
    planning = (
        db.query(Planning)
        .options(joinedload(Planning.profil))
        .filter(Planning.id == planning_id)
        .first()
    )
    if not planning:
        raise HTTPException(status_code=404, detail="Planning introuvable")
    if not _utilisateur_accede_profil(db, utilisateur, planning.profil):
        raise HTTPException(status_code=403, detail="Accès refusé à ce planning")
    return planning
