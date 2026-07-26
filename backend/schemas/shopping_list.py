from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.schemas.ingredient import IngredientOut
from backend.schemas.point_de_vente import PointDeVenteOut

PeriodeCourses = Literal["jour", "semaine", "mois"]
StatutCourses = Literal["disponible", "à acheter"]


class ListeCoursesPeriodeItem(BaseModel):
    ingredient: IngredientOut
    categorie: str
    quantite_totale_requise: float
    quantite_disponible: float
    quantite_a_acheter: float
    unite: str
    statut: StatutCourses


class DetailCoutIngredient(BaseModel):
    ingredient_id: str
    ingredient_nom: str
    quantite_a_acheter: float
    unite: str
    prix_unitaire: float
    cout_estime: float
    source_prix: Literal["offre", "reference"]
    point_de_vente: Optional[PointDeVenteOut] = None


class EstimationCoutListe(BaseModel):
    cout_total_estime: float
    details_par_ingredient: list[DetailCoutIngredient] = Field(default_factory=list)
    marches_a_visiter: list[PointDeVenteOut] = Field(default_factory=list)


class ListeCoursesPeriodeResponse(BaseModel):
    periode: PeriodeCourses
    date_debut: str
    jours_couverts: int
    items: list[ListeCoursesPeriodeItem]
    estimation: Optional[EstimationCoutListe] = None
    message: str = ""
