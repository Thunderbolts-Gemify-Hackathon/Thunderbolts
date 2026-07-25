"""Dépendances FastAPI : auth minimale par token API."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.planning import Planning, RepasPlanifie
from backend.models.profil import Profil
from backend.models.utilisateur import Utilisateur


def get_current_utilisateur(
    db: Session = Depends(get_db),
    x_api_token: str = Header(..., alias="X-API-Token"),
) -> Utilisateur:
    if not x_api_token.strip():
        raise HTTPException(status_code=401, detail="Token API manquant")
    utilisateur = (
        db.query(Utilisateur).filter(Utilisateur.api_token == x_api_token.strip()).first()
    )
    if not utilisateur:
        raise HTTPException(status_code=401, detail="Token API invalide")
    return utilisateur


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
    if repas.planning.profil.utilisateur_id != utilisateur.id:
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
    if planning.profil.utilisateur_id != utilisateur.id:
        raise HTTPException(status_code=403, detail="Accès refusé à ce planning")
    return planning
