import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.profil import Profil


class DefiProgress(Base):
    __tablename__ = "defi_progress"
    __table_args__ = (
        UniqueConstraint("profil_id", "defi_id", name="uq_defi_progress_profil"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profil_id: Mapped[str] = mapped_column(String(36), ForeignKey("profils.id"), nullable=False)
    defi_id: Mapped[str] = mapped_column(String(64), nullable=False)
    valeur: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    profil: Mapped["Profil"] = relationship()
