from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.composites import ListeCoursesItem
from backend.schemas.planning import PeriodePlanning, PlanningOut, RepasPlanifieOut
from backend.services import planning_service

router = APIRouter(prefix="/planning", tags=["planning"])


@router.get("/{profil_id}", response_model=PlanningOut)
def get_planning(
    profil_id: str,
    periode: PeriodePlanning = Query("semaine"),
    date_debut: date = Query(...),
    db: Session = Depends(get_db),
):
    planning = planning_service.get_planning(db, profil_id, periode, date_debut)
    if planning is None:
        raise HTTPException(status_code=404, detail="Planning introuvable")
    return planning


@router.post("/{repas_id}/valider", response_model=RepasPlanifieOut)
def valider_repas(repas_id: str, db: Session = Depends(get_db)):
    return planning_service.valider_repas(db, repas_id)


@router.post("/{repas_id}/annuler", response_model=RepasPlanifieOut)
def annuler_validation(repas_id: str, db: Session = Depends(get_db)):
    return planning_service.annuler_validation(db, repas_id)


@router.get("/{planning_id}/courses", response_model=list[ListeCoursesItem])
def liste_courses(planning_id: str, db: Session = Depends(get_db)):
    return planning_service.get_liste_courses(db, planning_id)
