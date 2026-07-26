from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.liste_course_item import ListeCourseItem
from backend.schemas.liste_course import ListeCourseItemCreate, ListeCourseItemUpdate
from backend.services import stock_service


def list_items(db: Session, profil_id: str, *, include_done: bool = False) -> list[ListeCourseItem]:
    q = db.query(ListeCourseItem).filter(ListeCourseItem.profil_id == profil_id)
    if not include_done:
        q = q.filter(ListeCourseItem.done.is_(False))
    return q.order_by(ListeCourseItem.label).all()


def create_item(db: Session, profil_id: str, payload: ListeCourseItemCreate) -> ListeCourseItem:
    item = ListeCourseItem(
        profil_id=profil_id,
        ingredient_id=payload.ingredient_id,
        label=payload.label.strip(),
        quantite=payload.quantite,
        unite=payload.unite,
        prix_estime=payload.prix_estime,
        custom=payload.custom,
        coche=False,
        done=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session, profil_id: str, item_id: str, payload: ListeCourseItemUpdate
) -> ListeCourseItem:
    item = (
        db.query(ListeCourseItem)
        .filter(ListeCourseItem.id == item_id, ListeCourseItem.profil_id == profil_id)
        .first()
    )
    if not item:
        raise ValueError("Article introuvable")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, profil_id: str, item_id: str) -> None:
    item = (
        db.query(ListeCourseItem)
        .filter(ListeCourseItem.id == item_id, ListeCourseItem.profil_id == profil_id)
        .first()
    )
    if not item:
        raise ValueError("Article introuvable")
    db.delete(item)
    db.commit()


def terminer_courses(
    db: Session,
    profil_id: str,
    item_ids: list[str] | None = None,
    *,
    label: str | None = "Courses",
) -> dict:
    """Approvisionne le stock pour les articles cochés (avec ingredient_id) et les marque done."""
    q = db.query(ListeCourseItem).filter(
        ListeCourseItem.profil_id == profil_id,
        ListeCourseItem.done.is_(False),
    )
    if item_ids:
        q = q.filter(ListeCourseItem.id.in_(item_ids))
    else:
        q = q.filter(ListeCourseItem.coche.is_(True))
    items = q.all()
    if not items:
        raise ValueError("Aucun article à terminer")

    appro_items = []
    for item in items:
        if item.ingredient_id:
            appro_items.append(
                {
                    "ingredient_id": item.ingredient_id,
                    "quantite": item.quantite,
                    "unite": item.unite,
                    "prix": item.prix_estime,
                }
            )

    result = {"stock": [], "depense": None, "montant_restant": 0.0}
    if appro_items:
        result = stock_service.approvisionner(
            db, profil_id, appro_items, label=label or "Courses"
        )

    for item in items:
        item.coche = True
        item.done = True
    db.commit()

    return {
        "items_termines": len(items),
        "stock_approvisionne": len(appro_items),
        "montant_restant": float(result.get("montant_restant") or 0),
    }
