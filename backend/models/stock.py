import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.ingredient import Ingredient
    from backend.models.profil import Profil


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profils.id"), unique=True, nullable=False
    )
    lieu_stockage: Mapped[str] = mapped_column(String(50), nullable=False, default="cuisine")
    derniere_mise_a_jour: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    profil: Mapped["Profil"] = relationship(back_populates="stock")
    ingredients: Mapped[list["IngredientStock"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )


class IngredientStock(Base):
    __tablename__ = "ingredient_stocks"
    __table_args__ = (
        UniqueConstraint("stock_id", "ingredient_id", name="uq_stock_ingredient"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_id: Mapped[str] = mapped_column(String(36), ForeignKey("stocks.id"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingredients.id"), nullable=False
    )
    quantite_disponible: Mapped[float] = mapped_column(Float, nullable=False)
    unite: Mapped[str] = mapped_column(String(10), nullable=False)
    date_peremption: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    stock: Mapped["Stock"] = relationship(back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="ingredient_stocks")
