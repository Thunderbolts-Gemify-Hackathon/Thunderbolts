from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    historique: list[ChatMessage] = Field(default_factory=list)


class ToolCallTrace(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    reponse: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)


class RemedeResponse(BaseModel):
    remede: str


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
