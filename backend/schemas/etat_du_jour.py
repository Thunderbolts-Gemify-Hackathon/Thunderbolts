from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


TypeEtatDuJour = Literal["fatigue", "stresse", "en_forme", "un_peu_malade", "normal"]


class EtatDuJourCreate(BaseModel):
    date: date
    type: TypeEtatDuJour


class EtatDuJourUpdate(BaseModel):
    date: Optional[date] = None
    type: Optional[TypeEtatDuJour] = None


class EtatDuJourOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    foyer_id: str
    date: date
    type: str
