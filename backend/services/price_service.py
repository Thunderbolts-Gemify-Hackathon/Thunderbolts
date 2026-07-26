from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.ingredient import Ingredient
from backend.models.price_report import PriceIndex, PriceReport
from backend.schemas.price import PriceReportCreate


def create_report(
    db: Session, profil_id: str | None, payload: PriceReportCreate
) -> PriceReport:
    if not db.get(Ingredient, payload.ingredient_id):
        raise ValueError("Ingrédient introuvable")
    jour = payload.jour or date.today()
    report = PriceReport(
        profil_id=profil_id,
        ingredient_id=payload.ingredient_id,
        quartier=payload.quartier.strip().lower(),
        prix=payload.prix,
        unite=payload.unite,
        jour=jour,
    )
    db.add(report)
    db.flush()
    _reaggregate(db, payload.ingredient_id, report.quartier, jour)
    db.commit()
    db.refresh(report)
    return report


def list_reports(
    db: Session,
    *,
    quartier: str | None = None,
    ingredient_id: str | None = None,
    limit: int = 50,
) -> list[PriceReport]:
    q = db.query(PriceReport)
    if quartier:
        q = q.filter(PriceReport.quartier == quartier.strip().lower())
    if ingredient_id:
        q = q.filter(PriceReport.ingredient_id == ingredient_id)
    return q.order_by(PriceReport.created_at.desc()).limit(limit).all()


def get_index(
    db: Session,
    *,
    quartier: str | None = None,
    ingredient_id: str | None = None,
    jour: date | None = None,
) -> list[PriceIndex]:
    q = db.query(PriceIndex)
    if quartier:
        q = q.filter(PriceIndex.quartier == quartier.strip().lower())
    if ingredient_id:
        q = q.filter(PriceIndex.ingredient_id == ingredient_id)
    if jour:
        q = q.filter(PriceIndex.jour == jour)
    return q.order_by(PriceIndex.jour.desc()).limit(100).all()


def get_local_price(
    db: Session,
    ingredient_nom: str,
    quartier: str | None = None,
) -> dict:
    ing = db.query(Ingredient).filter(Ingredient.nom.ilike(ingredient_nom.strip())).first()
    if not ing:
        raise ValueError(f"Ingrédient introuvable: {ingredient_nom}")
    q = db.query(PriceIndex).filter(PriceIndex.ingredient_id == ing.id)
    if quartier:
        q = q.filter(PriceIndex.quartier == quartier.strip().lower())
    idx = q.order_by(PriceIndex.jour.desc()).first()
    if idx:
        return {
            "ingredient": ing.nom,
            "prix_moyen": idx.prix_moyen,
            "quartier": idx.quartier,
            "jour": str(idx.jour),
            "source": "crowd",
            "nb_rapports": idx.nb_rapports,
        }
    return {
        "ingredient": ing.nom,
        "prix_moyen": ing.prix_moyen_reference,
        "quartier": quartier,
        "jour": None,
        "source": "catalogue",
        "nb_rapports": 0,
    }


def _reaggregate(db: Session, ingredient_id: str, quartier: str, jour: date) -> None:
    row = (
        db.query(
            func.avg(PriceReport.prix).label("moy"),
            func.count(PriceReport.id).label("n"),
        )
        .filter(
            PriceReport.ingredient_id == ingredient_id,
            PriceReport.quartier == quartier,
            PriceReport.jour == jour,
        )
        .one()
    )
    idx = (
        db.query(PriceIndex)
        .filter(
            PriceIndex.ingredient_id == ingredient_id,
            PriceIndex.quartier == quartier,
            PriceIndex.jour == jour,
        )
        .first()
    )
    if idx:
        idx.prix_moyen = float(row.moy or 0)
        idx.nb_rapports = int(row.n or 0)
    else:
        db.add(
            PriceIndex(
                ingredient_id=ingredient_id,
                quartier=quartier,
                jour=jour,
                prix_moyen=float(row.moy or 0),
                nb_rapports=int(row.n or 0),
            )
        )
