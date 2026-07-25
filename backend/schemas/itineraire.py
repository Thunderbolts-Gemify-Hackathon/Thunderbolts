from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


NiveauSecurite = Literal["sur", "prudence", "a_eviter"]
ModeDeplacement = Literal["pied", "voiture", "moto"]


class ItineraireCreate(BaseModel):
    point_de_vente_id: str
    profil_id: Optional[str] = None
    distance: float = Field(ge=0)
    niveau_securite: NiveauSecurite
    mode_deplacement: ModeDeplacement


class ItineraireUpdate(BaseModel):
    profil_id: Optional[str] = None
    distance: Optional[float] = Field(default=None, ge=0)
    niveau_securite: Optional[NiveauSecurite] = None
    mode_deplacement: Optional[ModeDeplacement] = None


class ItineraireOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    point_de_vente_id: str
    profil_id: Optional[str] = None
    distance: float
    niveau_securite: str
    mode_deplacement: str
