import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.budget import Budget
    from backend.models.profil import Profil


class Preferences(Base):
    __tablename__ = "preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profils.id"), unique=True, nullable=False
    )
    tabous: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    allergies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    severite_allergie: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    regime_specifique: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    aliments_detestes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    profil: Mapped["Profil"] = relationship(back_populates="preferences")
    budget: Mapped[Optional["Budget"]] = relationship(
        back_populates="preferences", uselist=False
    )
