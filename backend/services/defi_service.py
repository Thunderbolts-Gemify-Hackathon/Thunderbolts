from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.defi_progress import DefiProgress
from backend.services import anti_gaspi_service

DEFIS = [
    {
        "id": "budget-semaine",
        "titre": "Semaine sous 50 000 Ar",
        "description": "Tiens ton budget courses sous 50 000 Ar cette semaine.",
        "type": "budget",
        "objectif": 50000,
        "unite": "Ar",
    },
    {
        "id": "anti-gaspi-3j",
        "titre": "Zéro gaspi 3 jours",
        "description": "Utilise tout ce qui périme dans les 3 jours.",
        "type": "anti_gaspi",
        "objectif": 3,
        "unite": "jours",
    },
    {
        "id": "fait-maison",
        "titre": "5 repas maison",
        "description": "Valide 5 repas cuisinés à la maison.",
        "type": "repas",
        "objectif": 5,
        "unite": "repas",
    },
]


def list_defis() -> list[dict]:
    return list(DEFIS)


def _get_or_create(db: Session, profil_id: str, defi_id: str) -> DefiProgress:
    row = (
        db.query(DefiProgress)
        .filter(DefiProgress.profil_id == profil_id, DefiProgress.defi_id == defi_id)
        .first()
    )
    if row:
        return row
    row = DefiProgress(profil_id=profil_id, defi_id=defi_id, valeur=0.0)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def sync_anti_gaspi_progress(db: Session, profil_id: str) -> DefiProgress:
    stats = anti_gaspi_service.compute_anti_gaspi(db, profil_id)
    streak = float(stats.get("streak_jours") or 0)
    row = _get_or_create(db, profil_id, "anti-gaspi-3j")
    if streak > row.valeur:
        row.valeur = streak
        db.commit()
        db.refresh(row)
    return row


def list_defis_with_progress(db: Session, profil_id: str | None) -> list[dict]:
    base = list_defis()
    if not profil_id:
        return [{**d, "progress": None} for d in base]
    sync_anti_gaspi_progress(db, profil_id)
    out = []
    for d in base:
        row = (
            db.query(DefiProgress)
            .filter(DefiProgress.profil_id == profil_id, DefiProgress.defi_id == d["id"])
            .first()
        )
        out.append(
            {
                **d,
                "progress": {
                    "valeur": row.valeur if row else 0.0,
                    "objectif": d["objectif"],
                    "atteint": (row.valeur if row else 0.0) >= float(d["objectif"]),
                },
            }
        )
    return out


def increment_progress(
    db: Session, profil_id: str, defi_id: str, increment: float = 1.0
) -> dict:
    ids = {d["id"] for d in DEFIS}
    if defi_id not in ids:
        raise ValueError("Défi inconnu")
    row = _get_or_create(db, profil_id, defi_id)
    row.valeur = float(row.valeur) + float(increment)
    db.commit()
    db.refresh(row)
    defi = next(d for d in DEFIS if d["id"] == defi_id)
    return {
        "defi_id": defi_id,
        "valeur": row.valeur,
        "objectif": defi["objectif"],
        "atteint": row.valeur >= float(defi["objectif"]),
    }
