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


def accept_invite(db: Session, invite_token: str, utilisateur_id: str) -> FoyerMembreLien:
    """Rattache l'utilisateur courant à l'invitation pending."""
    invite = (
        db.query(FoyerMembreLien)
        .filter(
            FoyerMembreLien.invite_token == invite_token,
            FoyerMembreLien.utilisateur_id.is_(None),
        )
        .first()
    )
    if not invite:
        raise ValueError("Invitation introuvable ou déjà utilisée")

    existing = (
        db.query(FoyerMembreLien)
        .filter(
            FoyerMembreLien.foyer_id == invite.foyer_id,
            FoyerMembreLien.utilisateur_id == utilisateur_id,
        )
        .first()
    )
    if existing:
        db.delete(invite)
        db.commit()
        return existing

    invite.utilisateur_id = utilisateur_id
    invite.role = "membre" if invite.role == "invite" else invite.role
    invite.invite_token = None
    db.commit()
    db.refresh(invite)
    return invite


def revoke_lien(db: Session, foyer_id: str, lien_id: str, requester_utilisateur_id: str) -> None:
    owner = (
        db.query(FoyerMembreLien)
        .filter(
            FoyerMembreLien.foyer_id == foyer_id,
            FoyerMembreLien.utilisateur_id == requester_utilisateur_id,
            FoyerMembreLien.role == "owner",
        )
        .first()
    )
    if not owner:
        raise ValueError("Seul le propriétaire peut retirer un membre")
    lien = db.get(FoyerMembreLien, lien_id)
    if not lien or lien.foyer_id != foyer_id:
        raise ValueError("Lien introuvable")
    if lien.role == "owner":
        raise ValueError("Impossible de retirer le propriétaire")
    db.delete(lien)
    db.commit()
