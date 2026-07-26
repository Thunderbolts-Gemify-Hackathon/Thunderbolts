from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from backend.schemas.recette import RecetteOut

TypeRepas = Literal["petit_dejeuner", "dejeuner", "diner"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    historique: list[ChatMessage] = Field(default_factory=list)
    voice: bool = False


class ToolCallTrace(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    reponse: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)


class RemedeResponse(BaseModel):
    remede: str


class EtapeRecette(BaseModel):
    numero: int
    titre: str
    ingredients: list[str] = Field(default_factory=list)


class EtapesRecetteResponse(BaseModel):
    etapes: list[EtapeRecette]


class DirectiveCoursesRequest(BaseModel):
    ingredient_id: Optional[str] = None
    ingredient_nom: Optional[str] = None
    rayon_km: float = Field(default=15, gt=0)

    @model_validator(mode="after")
    def require_ingredient_ref(self) -> "DirectiveCoursesRequest":
        if not self.ingredient_id and not (self.ingredient_nom and self.ingredient_nom.strip()):
            raise ValueError("ingredient_id ou ingredient_nom requis")
        return self


class DirectiveCoursesResponse(BaseModel):
    ingredient_id: str
    ingredient_nom: str
    point_de_vente: str
    type_pdv: str
    prix: float
    devise: str = "Ar"
    distance_km: Optional[float] = None
    niveau_securite: Optional[str] = None
    mode_deplacement: Optional[str] = None
    deprioritise: bool = False
    phrase: str


class SuggestionRepasRequest(BaseModel):
    type_repas: Optional[TypeRepas] = None
    duree_max_minutes: Optional[int] = Field(default=None, gt=0)


class SuggestionRepasResponse(BaseModel):
    recette: RecetteOut
    type_repas: TypeRepas
    message: str
    couverture_stock: float
    ingredients_manquants: list[str] = Field(default_factory=list)
