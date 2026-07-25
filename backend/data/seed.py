from __future__ import annotations

from sqlalchemy.orm import Session

from backend.data.catalog import INGREDIENTS, ITINERAIRES, POINTS_DE_VENTE, RECETTES
from backend.data.seed_food import seed_food
from backend.data.seed_markets import seed_markets
from backend.database import SessionLocal, init_db


def seed(db: Session | None = None) -> dict[str, int]:
    own = db is None
    if own:
        init_db()
        db = SessionLocal()

    try:
        ingredients = seed_food(db)
        seed_markets(db, ingredients)
        db.commit()
        return {
            "ingredients": len(INGREDIENTS),
            "recettes": len(RECETTES),
            "points_de_vente": len(POINTS_DE_VENTE),
            "itineraires": len(ITINERAIRES),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    print(seed())
