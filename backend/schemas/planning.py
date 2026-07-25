from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PeriodePlanning = Literal["semaine", "mois"]


class RepasPlanifieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    planning_id: str
    recette_id: str
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
