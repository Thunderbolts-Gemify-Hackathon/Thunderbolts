"""Migrations SQLite légères (ALTER TABLE) après create_all — sans Alembic."""

from __future__ import annotations

import uuid

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

# table -> [(colonne, ddl SQL type + contraintes légères)]
_COLONNES = {
    "utilisateurs": [
        ("api_token", "VARCHAR(64)"),
    ],
    "profils": [
        ("utilisateur_id", "VARCHAR(36)"),
    ],
    "preferences": [
        ("aliments_aimes", "JSON"),
    ],
    "membres_foyer": [
        ("prenom", "VARCHAR(100)"),
        ("lien", "VARCHAR(40)"),
    ],
    "recettes": [
        ("instructions", "VARCHAR(2000)"),
    ],
    "budgets": [
        ("devise", "VARCHAR(10) DEFAULT 'Ar'"),
    ],
}


def migrate_sqlite(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, colonnes in _COLONNES.items():
            if table not in tables:
                continue
            existantes = {c["name"] for c in inspector.get_columns(table)}
            for nom, ddl in colonnes:
                if nom in existantes:
                    continue
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {nom} {ddl}"))

        # Backfill tokens manquants
        if "utilisateurs" in tables:
            rows = conn.execute(
                text("SELECT id FROM utilisateurs WHERE api_token IS NULL OR api_token = ''")
            ).fetchall()
            for (uid,) in rows:
                conn.execute(
                    text("UPDATE utilisateurs SET api_token = :t WHERE id = :id"),
                    {"t": uuid.uuid4().hex, "id": uid},
                )

        # Backfill devise
        if "budgets" in tables:
            conn.execute(text("UPDATE budgets SET devise = 'Ar' WHERE devise IS NULL OR devise = ''"))

        # Backfill aliments_aimes JSON vide
        if "preferences" in tables:
            conn.execute(
                text(
                    "UPDATE preferences SET aliments_aimes = '[]' "
                    "WHERE aliments_aimes IS NULL"
                )
            )
