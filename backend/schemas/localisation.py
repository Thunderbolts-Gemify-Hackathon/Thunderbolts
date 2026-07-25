from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


Saison = Literal["ete_humide", "hiver_sec", "intersaison"]


class LocalisationCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    quartier: Optional[str] = None
    saison: Optional[Saison] = None


class LocalisationUpdate(BaseModel):
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    quartier: Optional[str] = None
    saison: Optional[Saison] = None


class LocalisationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    latitude: float
    longitude: float
    quartier: Optional[str] = None
    saison: Optional[str] = None
