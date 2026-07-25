import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.ingredient import Ingredient
    from backend.models.itineraire import Itineraire


class PointDeVente(Base):
    __tablename__ = "points_de_vente"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    horaires_verifies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    offres: Mapped[list["Offre"]] = relationship(
        back_populates="point_de_vente", cascade="all, delete-orphan"
    )
    itineraires: Mapped[list["Itineraire"]] = relationship(back_populates="point_de_vente")


class Offre(Base):
    __tablename__ = "offres"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    point_de_vente_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("points_de_vente.id"), nullable=False
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingredients.id"), nullable=False
    )
    prix: Mapped[float] = mapped_column(Float, nullable=False)
    derniere_mise_a_jour: Mapped[date] = mapped_column(Date, nullable=False)

    point_de_vente: Mapped["PointDeVente"] = relationship(back_populates="offres")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="offres")
