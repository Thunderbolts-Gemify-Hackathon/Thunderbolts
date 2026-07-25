from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


TypePointDeVente = Literal["grande_surface", "epicerie", "grossiste"]


class PointDeVenteCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    type: TypePointDeVente
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    horaires_verifies: bool = False


class PointDeVenteUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=200)
    type: Optional[TypePointDeVente] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    horaires_verifies: Optional[bool] = None


class PointDeVenteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    type: str
    latitude: float
    longitude: float
    horaires_verifies: bool


class OffreCreate(BaseModel):
    point_de_vente_id: str
    ingredient_id: str
    prix: float = Field(ge=0)
    derniere_mise_a_jour: date


class OffreUpdate(BaseModel):
    prix: Optional[float] = Field(default=None, ge=0)
    derniere_mise_a_jour: Optional[date] = None


class OffreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    point_de_vente_id: str
    ingredient_id: str
    prix: float
    derniere_mise_a_jour: date
