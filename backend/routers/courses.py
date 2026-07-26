from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_profil_owner
from backend.models.profil import Profil
from backend.schemas.liste_course import (
    CoursesTerminerRequest,
    CoursesTerminerResponse,
    ListeCourseItemCreate,
    ListeCourseItemOut,
    ListeCourseItemUpdate,
)
from backend.services import liste_course_service

router = APIRouter(prefix="/planning", tags=["courses"])


@router.get("/{profil_id}/courses/items", response_model=list[ListeCourseItemOut])
def list_course_items(
    profil: Profil = Depends(require_profil_owner),
    include_done: bool = False,
    db: Session = Depends(get_db),
):
    return liste_course_service.list_items(db, profil.id, include_done=include_done)


@router.post(
    "/{profil_id}/courses/items",
    response_model=ListeCourseItemOut,
    status_code=201,
)
def create_course_item(
    payload: ListeCourseItemCreate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    return liste_course_service.create_item(db, profil.id, payload)


@router.patch(
    "/{profil_id}/courses/items/{item_id}",
    response_model=ListeCourseItemOut,
)
def update_course_item(
    item_id: str,
    payload: ListeCourseItemUpdate,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        return liste_course_service.update_item(db, profil.id, item_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{profil_id}/courses/items/{item_id}", status_code=204)
def delete_course_item(
    item_id: str,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        liste_course_service.delete_item(db, profil.id, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/{profil_id}/courses/terminer",
    response_model=CoursesTerminerResponse,
)
def terminer_courses(
    payload: CoursesTerminerRequest,
    profil: Profil = Depends(require_profil_owner),
    db: Session = Depends(get_db),
):
    try:
        return liste_course_service.terminer_courses(
            db, profil.id, payload.item_ids or None, label=payload.label
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
