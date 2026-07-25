import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.foyer import Foyer


class EtatDuJour(Base):
    __tablename__ = "etats_du_jour"
    __table_args__ = (UniqueConstraint("foyer_id", "date", name="uq_etat_foyer_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    foyer_id: Mapped[str] = mapped_column(String(36), ForeignKey("foyers.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)

    foyer: Mapped["Foyer"] = relationship(back_populates="etats_du_jour")
