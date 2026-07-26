from pydantic import BaseModel, ConfigDict


class FavoriRecetteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profil_id: str
    recette_id: str


class FavoriToggleOut(BaseModel):
    favori: bool
    recette_id: str
