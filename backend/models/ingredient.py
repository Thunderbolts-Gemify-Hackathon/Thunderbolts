import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
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

    ingredient_stocks: Mapped[list["IngredientStock"]] = relationship(back_populates="ingredient")
    recette_ingredients: Mapped[list["RecetteIngredient"]] = relationship(
        back_populates="ingredient"
    )
    offres: Mapped[list["Offre"]] = relationship(back_populates="ingredient")
