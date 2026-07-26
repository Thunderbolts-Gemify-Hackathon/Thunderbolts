from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.recette import Recette
from backend.models.repas_feedback import RepasFeedback
from backend.schemas.feedback import RepasFeedbackCreate


def upsert_feedback(
    db: Session, profil_id: str, payload: RepasFeedbackCreate
) -> RepasFeedback:
    if not db.get(Recette, payload.recette_id):
        raise ValueError("Recette introuvable")
    if payload.note == 0:
        raise ValueError("note doit être -1 ou 1")
    existing = (
        db.query(RepasFeedback)
        .filter(
            RepasFeedback.profil_id == profil_id,
            RepasFeedback.recette_id == payload.recette_id,
        )
        .first()
    )
    if existing:
        existing.note = payload.note
        existing.commentaire = payload.commentaire
        db.commit()
        db.refresh(existing)
        return existing
    fb = RepasFeedback(
        profil_id=profil_id,
        recette_id=payload.recette_id,
        note=payload.note,
        commentaire=payload.commentaire,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


def liked_recette_ids(db: Session, profil_id: str) -> set[str]:
    rows = (
        db.query(RepasFeedback.recette_id)
        .filter(RepasFeedback.profil_id == profil_id, RepasFeedback.note > 0)
        .all()
    )
    return {r[0] for r in rows}


def disliked_recette_ids(db: Session, profil_id: str) -> set[str]:
    rows = (
        db.query(RepasFeedback.recette_id)
        .filter(RepasFeedback.profil_id == profil_id, RepasFeedback.note < 0)
        .all()
    )
    return {r[0] for r in rows}
