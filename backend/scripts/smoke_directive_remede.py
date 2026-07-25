"""Smoke sans Ollama : directive courses + etat malade (remede nécessite Gemma)."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from backend.data.seed import seed
from backend.database import SessionLocal, init_db
from backend.main import app
from backend.models.foyer import Foyer, MembreFoyer
from backend.models.localisation import Localisation
from backend.models.preferences import Preferences
from backend.models.profil import Profil
from backend.models.utilisateur import Utilisateur
import uuid


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed(db)
        user = Utilisateur(
            nom="Smoke",
            prenom="Demo",
            email=f"smoke-{uuid.uuid4().hex[:8]}@example.com",
            date_naissance=date(1995, 1, 1),
            api_token=uuid.uuid4().hex,
        )
        db.add(user)
        db.flush()
        profil = Profil(
            utilisateur_id=user.id,
            age=30,
            sexe="homme",
            poids=70,
            taille=175,
            niveau_activite="modere",
            objectif="maintien",
        )
        db.add(profil)
        db.flush()
        db.add(Preferences(profil_id=profil.id, allergies=[], tabous=[], aliments_aimes=["poulet"]))
        foyer = Foyer(profil_id=profil.id, nombre_personnes=1)
        db.add(foyer)
        db.flush()
        db.add(MembreFoyer(foyer_id=foyer.id, age_approx=30, regime_aligne=True))
        db.add(
            Localisation(
                profil_id=profil.id,
                latitude=-18.9102,
                longitude=47.5256,
                quartier="Analakely",
            )
        )
        db.commit()
        headers = {"X-API-Token": user.api_token}
        client = TestClient(app)

        r = client.post(
            f"/ia/{profil.id}/directive-courses",
            headers=headers,
            json={"ingredient_nom": "poulet"},
        )
        assert r.status_code == 200, r.text
        phrase = r.json()["phrase"]
        print("directive_ok:", phrase)

        r = client.post(
            f"/onboarding/profil/{profil.id}/etat-du-jour",
            headers=headers,
            json={"date": date.today().isoformat(), "type": "un_peu_malade"},
        )
        assert r.status_code == 201, r.text
        print("etat_malade_ok")

        print("SMOKE_OK (chat/remede Gemma: tester via app si Ollama tourne)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
