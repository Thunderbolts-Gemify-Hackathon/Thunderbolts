import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.preferences import Preferences


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    preferences_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("preferences.id"), unique=True, nullable=False
    )
    montant: Mapped[float] = mapped_column(Float, nullable=False)
    periode: Mapped[str] = mapped_column(String(20), nullable=False)
    montant_restant: Mapped[float] = mapped_column(Float, nullable=False)
    devise: Mapped[str] = mapped_column(String(10), nullable=False, default="Ar")

    preferences: Mapped["Preferences"] = relationship(back_populates="budget")
