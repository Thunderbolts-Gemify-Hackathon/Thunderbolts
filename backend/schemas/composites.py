from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.ingredient import IngredientOut
from backend.schemas.itineraire import ItineraireOut
from backend.schemas.point_de_vente import PointDeVenteOut


class StockDeductionRequest(BaseModel):
    ingredient_id: str
    quantite: float = Field(gt=0)


class CheckBudgetResponse(BaseModel):
    disponible: bool
    montant_restant: float
    cout_estime: float


class MarketMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    point_de_vente: PointDeVenteOut
    prix: float
    itineraire: Optional[ItineraireOut] = None
    deprioritise: bool = False
    prix_crowd: Optional[float] = None
    ecart_crowd_pct: Optional[float] = None


class PointDeVenteProcheOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    point_de_vente: PointDeVenteOut
    distance_km: float
    itineraire: Optional[ItineraireOut] = None
    deprioritise: bool = False


class RuptureOut(BaseModel):
    ingredient: IngredientOut
    quantite_manquante: float
    marches_suggeres: list[MarketMatchOut] = Field(default_factory=list)


class ListeCoursesItem(BaseModel):
    ingredient: IngredientOut
    poids_total_requis: float
    stock_disponible: float
    statut: Literal["disponible", "à acheter"]
