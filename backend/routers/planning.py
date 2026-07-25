from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_planning_owner, require_profil_owner, require_repas_owner
from backend.models.planning import Planning, RepasPlanifie
from backend.models.profil import Profil
from backend.schemas.composites import ListeCoursesItem
from backend.schemas.planning import PeriodePlanning, PlanningOut, RepasPlanifieOut
from backend.services import courses_service, planning_service

router = APIRouter(prefix="/planning", tags=["planning"])


@router.get("/{profil_id}", response_model=PlanningOut)
def get_planning(
    profil: Profil = Depends(require_profil_owner),
    periode: PeriodePlanning = Query("semaine"),
    date_debut: date = Query(...),
    db: Session = Depends(get_db),
):
    planning = planning_service.get_planning(db, profil.id, periode, date_debut)
    if planning is None:
        raise HTTPException(status_code=404, detail="Planning introuvable")
    return planning


@router.post("/{repas_id}/valider", response_model=RepasPlanifieOut)
def valider_repas(
    repas: RepasPlanifie = Depends(require_repas_owner),
    db: Session = Depends(get_db),
):
    return planning_service.valider_repas(db, repas.id)


@router.post("/{repas_id}/annuler", response_model=RepasPlanifieOut)
def annuler_validation(
    repas: RepasPlanifie = Depends(require_repas_owner),
    db: Session = Depends(get_db),
):
    return planning_service.annuler_validation(db, repas.id)


@router.get("/{planning_id}/courses", response_model=list[ListeCoursesItem])
def liste_courses(
    planning: Planning = Depends(require_planning_owner),
    db: Session = Depends(get_db),
):
    return courses_service.get_liste_courses(db, planning.id)
