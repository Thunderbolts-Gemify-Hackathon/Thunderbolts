import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.point_de_vente import Offre
    from backend.models.recette import RecetteIngredient
    from backend.models.stock import IngredientStock


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    unite_defaut: Mapped[str] = mapped_column(String(10), nullable=False)
    categorie: Mapped[str] = mapped_column(String(30), nullable=False, default="autre")
    conservation_jours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    saison: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    # Prix de référence au kg / L / unité (fallback si aucune Offre marché).
    prix_moyen_reference: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    ingredient_stocks: Mapped[list["IngredientStock"]] = relationship(back_populates="ingredient")
    recette_ingredients: Mapped[list["RecetteIngredient"]] = relationship(
        back_populates="ingredient"
    )
    offres: Mapped[list["Offre"]] = relationship(back_populates="ingredient")
