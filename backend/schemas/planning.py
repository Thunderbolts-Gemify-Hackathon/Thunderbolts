from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


PeriodePlanning = Literal["semaine", "mois"]
TypeRepas = Literal["petit_dejeuner", "dejeuner", "diner", "collation"]
StatutRepas = Literal["planifie", "consomme", "annule"]


class PlanningCreate(BaseModel):
    profil_id: str
    periode: PeriodePlanning
    date_debut: date


class PlanningUpdate(BaseModel):
    periode: Optional[PeriodePlanning] = None
    date_debut: Optional[date] = None


class PlanningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    periode: str
    date_debut: date
    repas: list["RepasPlanifieOut"] = Field(default_factory=list)


class RepasPlanifieCreate(BaseModel):
    planning_id: str
    recette_id: str
    jour: date
    type_repas: TypeRepas
    statut: StatutRepas = "planifie"


class RepasPlanifieUpdate(BaseModel):
    jour: Optional[date] = None
    type_repas: Optional[TypeRepas] = None
    statut: Optional[StatutRepas] = None
    recette_id: Optional[str] = None


class RepasPlanifieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    planning_id: str
    recette_id: str
    jour: date
    type_repas: str
    statut: str


PlanningOut.model_rebuild()
