from typing import Any, Optional

from pydantic import BaseModel, Field


class PanierItemIn(BaseModel):
    ingredient_nom: str
    quantite: float = Field(gt=0)
    unite: str = "g"
    ingredient_id: Optional[str] = None


class PanierCheckRequest(BaseModel):
    items: list[PanierItemIn] = Field(min_length=1)
    budget: float = Field(gt=0)
    quartier: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class PanierSwapSuggestion(BaseModel):
    ingredient_nom: str
    alternative: str
    economie_estimee: float
    raison: str


class PanierCheckResponse(BaseModel):
    cout_estime: float
    budget: float
    ecart: float
    statut: str  # sous_budget | au_budget | over_budget
    swaps: list[PanierSwapSuggestion] = Field(default_factory=list)


class OneTripRequest(BaseModel):
    items: list[PanierItemIn] = Field(min_length=1)
    lat: float
    lon: float
    rayon_km: float = Field(default=15, gt=0, le=50)
    budget: Optional[float] = Field(default=None, gt=0)
    profil_id: Optional[str] = None


class OneTripStopItem(BaseModel):
    ingredient_id: str
    ingredient_nom: str
    quantite: float
    unite: str
    prix_unitaire: float
    cout_estime: float


class OneTripPdv(BaseModel):
    id: str
    nom: str
    type: str
    latitude: float
    longitude: float


class OneTripStop(BaseModel):
    point_de_vente: OneTripPdv
    distance_km: float
    cout_estime: float
    items: list[OneTripStopItem]


class OneTripManquant(BaseModel):
    ingredient_id: str
    ingredient_nom: str
    raison: str


class OneTripResponse(BaseModel):
    nb_arrets: int
    distance_totale_km: float
    cout_estime: float
    budget: Optional[float] = None
    ecart: Optional[float] = None
    statut: str
    stops: list[OneTripStop]
    manquants: list[OneTripManquant] = Field(default_factory=list)
    message: str
