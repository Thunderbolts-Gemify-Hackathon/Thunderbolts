import uuid
from datetime import time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.ingredient import Ingredient
    from backend.models.planning import RepasPlanifie
    from backend.models.profil import Profil


class Recette(Base):
    __tablename__ = "recettes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    heure_conseillee: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    kcal_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    proteines: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    glucides: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lipides: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duree_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    instructions: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    owner_profil_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profils.id"), nullable=True
    )

    ingredients: Mapped[list["RecetteIngredient"]] = relationship(
        back_populates="recette", cascade="all, delete-orphan"
    )
    repas_planifies: Mapped[list["RepasPlanifie"]] = relationship(back_populates="recette")
    owner: Mapped[Optional["Profil"]] = relationship(back_populates="recettes_creees")


class RecetteIngredient(Base):
    __tablename__ = "recette_ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recette_id: Mapped[str] = mapped_column(String(36), ForeignKey("recettes.id"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingredients.id"), nullable=False
    )
    poids_requis: Mapped[float] = mapped_column(Float, nullable=False)
    unite: Mapped[str] = mapped_column(String(10), nullable=False)

    recette: Mapped["Recette"] = relationship(back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recette_ingredients")
