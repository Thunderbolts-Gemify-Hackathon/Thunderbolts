import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent

load_dotenv(ROOT_DIR / ".env")


def build_database_url() -> str:
    return os.getenv("DATABASE_URL") or f"sqlite:///{BACKEND_DIR / 'kalitao.db'}"


DATABASE_URL = build_database_url()
# SQLite refuse le partage de connexion entre threads; FastAPI en ouvre plusieurs.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from backend import models  # noqa: F401
    from backend.db_migrate import migrate_sqlite
    from backend.services.market_service import backfill_offres_manquantes

    Base.metadata.create_all(bind=engine)
    migrate_sqlite(engine)

    db = SessionLocal()
    try:
        backfill_offres_manquantes(db)
    finally:
        db.close()
