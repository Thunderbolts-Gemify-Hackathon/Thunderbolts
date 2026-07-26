from __future__ import annotations

import secrets

from sqlalchemy.orm import Session

from backend.models.foyer import Foyer
from backend.models.foyer_membre_lien import FoyerMembreLien
from backend.models.profil import Profil


def list_liens(db: Session, foyer_id: str) -> list[FoyerMembreLien]:
    return (
        db.query(FoyerMembreLien)
        .filter(FoyerMembreLien.foyer_id == foyer_id)
        .order_by(FoyerMembreLien.created_at)
        .all()
    )


def create_invite(db: Session, profil_id: str, role: str = "invite") -> dict:
    profil = db.get(Profil, profil_id)
    if not profil or not profil.utilisateur_id:
        raise ValueError("Profil sans utilisateur")
    foyer = db.query(Foyer).filter(Foyer.profil_id == profil_id).first()
    if not foyer:
        raise ValueError("Foyer introuvable")

    owner = (
        db.query(FoyerMembreLien)
        .filter(
            FoyerMembreLien.foyer_id == foyer.id,
            FoyerMembreLien.utilisateur_id == profil.utilisateur_id,
            FoyerMembreLien.role == "owner",
        )
        .first()
    )
    if not owner:
        owner = FoyerMembreLien(
            utilisateur_id=profil.utilisateur_id,
            foyer_id=foyer.id,
            role="owner",
        )
        db.add(owner)

    token = secrets.token_urlsafe(16)
    # Stub : invitation en attente (pas encore d'utilisateur cible)
    invite = FoyerMembreLien(
        utilisateur_id=None,
        foyer_id=foyer.id,
        role=role if role in ("membre", "invite") else "invite",
        invite_token=token,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return {
        "lien": invite,
        "invite_url": f"kalitao://foyer/invite/{token}",
    }
