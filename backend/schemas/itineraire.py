from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItineraireOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    point_de_vente_id: str
    profil_id: Optional[str] = None
    distance: float
    niveau_securite: str
    mode_deplacement: str
