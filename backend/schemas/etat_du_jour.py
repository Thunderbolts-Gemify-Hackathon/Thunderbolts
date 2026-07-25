from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

TypeEtatDuJour = Literal["fatigue", "stresse", "en_forme", "un_peu_malade", "normal"]


class EtatDuJourCreate(BaseModel):
    date: date
    type: TypeEtatDuJour


class EtatDuJourOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    foyer_id: str
    date: date
    type: str
