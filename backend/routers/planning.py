from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_planning_owner, require_profil_owner, require_repas_owner
from backend.models.planning import Planning, RepasPlanifie
from backend.models.profil import Profil
from backend.schemas.composites import ListeCoursesItem
from backend.schemas.ingredient import IngredientOut
from backend.schemas.planning import PeriodePlanning, PlanningOut, RepasPlanifieOut
from backend.schemas.shopping_list import (
    DetailCoutIngredient,
    EstimationCoutListe,
    ListeCoursesPeriodeItem,
    ListeCoursesPeriodeResponse,
    PeriodeCourses,
)
from backend.services import courses_service, planning_service, shopping_list_service

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


@router.get(
    "/{profil_id}/liste-courses",
    response_model=ListeCoursesPeriodeResponse,
)
def liste_courses_periode(
    profil: Profil = Depends(require_profil_owner),
    periode: PeriodeCourses = Query("semaine"),
    date_debut: date = Query(...),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    """Liste de courses (quantites/prix deterministes) + message Gemma pour la phraser."""
    try:
        items_raw = shopping_list_service.generer_liste_courses_periode(
            db, profil.id, periode, date_debut
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    items = [
        ListeCoursesPeriodeItem(
            ingredient=IngredientOut.model_validate(row["ingredient"]),
            categorie=row["categorie"],
            quantite_totale_requise=row["quantite_totale_requise"],
            quantite_disponible=row["quantite_disponible"],
            quantite_a_acheter=row["quantite_a_acheter"],
            unite=row["unite"],
            statut=row["statut"],
        )
        for row in items_raw
    ]

    estimation = None
    use_lat, use_lon = lat, lon
    if use_lat is None or use_lon is None:
        loc = shopping_list_service.localisation_profil(db, profil.id)
        if loc is not None:
            use_lat, use_lon = loc.latitude, loc.longitude

    if use_lat is not None and use_lon is not None:
        raw_est = shopping_list_service.estimer_cout_liste(
            db, items_raw, use_lat, use_lon, profil_id=profil.id
        )
        estimation = EstimationCoutListe(
            cout_total_estime=raw_est["cout_total_estime"],
            details_par_ingredient=[
                DetailCoutIngredient(**d) for d in raw_est["details_par_ingredient"]
            ],
            marches_a_visiter=raw_est["marches_a_visiter"],
        )

    message = shopping_list_service.phraser_liste_via_gemma(items_raw, periode)

    return ListeCoursesPeriodeResponse(
        periode=periode,
        date_debut=date_debut.isoformat(),
        jours_couverts=shopping_list_service.JOURS_PAR_PERIODE[periode],
        items=items,
        estimation=estimation,
        message=message,
    )


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
