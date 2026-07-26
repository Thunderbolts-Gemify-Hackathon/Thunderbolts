from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.recette import RecetteOut

PeriodePlanning = Literal["jour", "semaine", "mois"]


class RepasPlanifieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    planning_id: str
    recette_id: str
    recette: RecetteOut
    jour: date
    type_repas: str
    statut: str


class PlanningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    periode: str
    date_debut: date
    repas: list[RepasPlanifieOut] = Field(default_factory=list)
