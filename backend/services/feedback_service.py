from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from backend.models.recette import Recette, RecetteIngredient
from backend.models.repas_feedback import RepasFeedback
from backend.schemas.feedback import RepasFeedbackCreate
from backend.services import foyer_agent_service

_TOP_INGREDIENTS = 5
_LIKE_IMPORTANCE = 1.5
_DISLIKE_IMPORTANCE = 1.4
_PREF_ING_IMPORTANCE = 1.1


def upsert_feedback(
    db: Session, profil_id: str, payload: RepasFeedbackCreate
) -> RepasFeedback:
    recette = (
        db.query(Recette)
        .options(joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient))
        .filter(Recette.id == payload.recette_id)
        .first()
    )
    if not recette:
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
        fb = existing
    else:
        fb = RepasFeedback(
            profil_id=profil_id,
            recette_id=payload.recette_id,
            note=payload.note,
            commentaire=payload.commentaire,
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

    _sync_memory_from_feedback(db, profil_id, recette, payload.note)
    return fb


def _sync_memory_from_feedback(
    db: Session, profil_id: str, recette: Recette, note: int
) -> None:
    if note > 0:
        foyer_agent_service.upsert_memory(
            db,
            profil_id,
            f"like:{recette.id}",
            f"Aime la recette {recette.nom}",
            importance=_LIKE_IMPORTANCE,
        )
        sign = "+"
    else:
        foyer_agent_service.upsert_memory(
            db,
            profil_id,
            f"dislike:{recette.id}",
            f"N'aime pas la recette {recette.nom}",
            importance=_DISLIKE_IMPORTANCE,
        )
        sign = "-"

    noms = []
    for ligne in recette.ingredients or []:
        if ligne.ingredient and ligne.ingredient.nom:
            noms.append(ligne.ingredient.nom.strip().lower())
    for nom in noms[:_TOP_INGREDIENTS]:
        foyer_agent_service.upsert_memory(
            db,
            profil_id,
            f"pref_ingredient:{nom}",
            f"{sign}{nom}",
            importance=_PREF_ING_IMPORTANCE,
        )


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
