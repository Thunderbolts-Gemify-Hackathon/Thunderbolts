import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.ingredient import Ingredient
    from backend.models.profil import Profil


class PriceReport(Base):
    __tablename__ = "price_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("profils.id"), nullable=True
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingredients.id"), nullable=False
    )
    quartier: Mapped[str] = mapped_column(String(100), nullable=False)
    prix: Mapped[float] = mapped_column(Float, nullable=False)
    unite: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    jour: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    profil: Mapped[Optional["Profil"]] = relationship(back_populates="price_reports")
    ingredient: Mapped["Ingredient"] = relationship()


class PriceIndex(Base):
    __tablename__ = "price_indexes"
    __table_args__ = (
        UniqueConstraint("ingredient_id", "quartier", "jour", name="uq_price_index_day"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ingredient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingredients.id"), nullable=False
    )
    quartier: Mapped[str] = mapped_column(String(100), nullable=False)
    jour: Mapped[date] = mapped_column(Date, nullable=False)
    prix_moyen: Mapped[float] = mapped_column(Float, nullable=False)
    nb_rapports: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    ingredient: Mapped["Ingredient"] = relationship()
