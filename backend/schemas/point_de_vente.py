from pydantic import BaseModel, ConfigDict


class PointDeVenteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    type: str
    latitude: float
    longitude: float
    horaires_verifies: bool
