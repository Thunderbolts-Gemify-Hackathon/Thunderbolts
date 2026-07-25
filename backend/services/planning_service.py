from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.services import stock_service


def get_planning(
    db: Session, profil_id: str, periode: str, date_debut: date
) -> Planning | None:
    return (
        db.query(Planning)
        .options(joinedload(Planning.repas).joinedload(RepasPlanifie.recette))
        .filter(
            Planning.profil_id == profil_id,
            Planning.periode == periode,
            Planning.date_debut == date_debut,
        )
        .first()
    )


def _repas_charge(db: Session, repas_planifie_id: str) -> RepasPlanifie:
    repas = (
        db.query(RepasPlanifie)
        .options(
            joinedload(RepasPlanifie.planning),
            joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient),
        )
        .filter(RepasPlanifie.id == repas_planifie_id)
        .first()
    )
    if not repas:
        raise HTTPException(status_code=404, detail="Repas planifié introuvable")
    return repas


def valider_repas(db: Session, repas_planifie_id: str) -> RepasPlanifie:
    repas = _repas_charge(db, repas_planifie_id)
    if repas.statut == "consomme":
        raise HTTPException(status_code=400, detail="Ce repas a déjà été validé")
    if repas.statut == "annule":
        raise HTTPException(status_code=400, detail="Impossible de valider un repas annulé")

    for ligne in repas.recette.ingredients:
        stock_service.update_stock(
            db, repas.planning.profil_id, ligne.ingredient_id, ligne.poids_requis, commit=False
        )
    repas.statut = "consomme"
    db.commit()
    db.refresh(repas)
    return repas


def annuler_validation(db: Session, repas_planifie_id: str) -> RepasPlanifie:
    repas = _repas_charge(db, repas_planifie_id)
    if repas.statut != "consomme":
        raise HTTPException(
            status_code=400, detail="Seule une validation (statut consomme) peut être annulée"
        )

    for ligne in repas.recette.ingredients:
        stock_service.recrediter_stock(
            db, repas.planning.profil_id, ligne.ingredient_id, ligne.poids_requis, commit=False
        )
    repas.statut = "planifie"
    db.commit()
    db.refresh(repas)
    return repas
