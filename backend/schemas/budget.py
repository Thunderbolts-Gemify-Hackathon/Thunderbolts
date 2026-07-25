from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PeriodeBudget = Literal["jour", "semaine", "mois"]


class BudgetCreate(BaseModel):
    montant: float = Field(gt=0)
    periode: PeriodeBudget
    montant_restant: Optional[float] = Field(default=None, ge=0)
    devise: str = "Ar"


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    preferences_id: str
    montant: float
    periode: str
    montant_restant: float
    devise: str
