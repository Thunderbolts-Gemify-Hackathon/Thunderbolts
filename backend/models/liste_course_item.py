import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.ingredient import Ingredient
    from backend.models.profil import Profil


class ListeCourseItem(Base):
    __tablename__ = "liste_course_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(String(36), ForeignKey("profils.id"), nullable=False)
    ingredient_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ingredients.id"), nullable=True
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    quantite: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    unite: Mapped[str] = mapped_column(String(20), nullable=False, default="u")
    prix_estime: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    coche: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profil: Mapped["Profil"] = relationship(back_populates="liste_course_items")
    ingredient: Mapped[Optional["Ingredient"]] = relationship()
