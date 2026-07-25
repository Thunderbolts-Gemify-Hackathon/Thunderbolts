from typing import Optional

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


class RuptureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient: IngredientOut
    quantite_manquante: float
    marches_suggeres: list[MarketMatchOut] = Field(default_factory=list)
