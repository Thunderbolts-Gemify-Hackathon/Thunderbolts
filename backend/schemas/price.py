from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PriceReportCreate(BaseModel):
    ingredient_id: str
    quartier: str = Field(min_length=1, max_length=100)
    prix: float = Field(gt=0)
    unite: str = Field(default="kg", max_length=20)
    jour: Optional[date] = None


class PriceReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: Optional[str] = None
    ingredient_id: str
    quartier: str
    prix: float
    unite: str
    jour: date
    created_at: datetime


class PriceIndexOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ingredient_id: str
    quartier: str
    jour: date
    prix_moyen: float
    nb_rapports: int
