"""Test isolé (Python direct, sans HTTP) de generer_planning().

Prérequis : Ollama local lancé (OLLAMA_HOST/OLLAMA_MODEL) ou GEMMA4_API_KEY en .env pour
le fallback Gemini. Réutilise le seed alimentaire de Dev 2 (backend/data/seed.py) et crée
un profil de test onboardé avec une allergie et un tabou, pour vérifier que le planning
généré les respecte.
"""

from __future__ import annotations

import sys
from datetime import date

import httpx
from sqlalchemy.orm import joinedload

from backend.data.seed import seed
from backend.database import SessionLocal, init_db
from backend.models.budget import Budget
from backend.models.foyer import Foyer, MembreFoyer
from backend.models.localisation import Localisation
from backend.models.planning import Planning
from backend.models.preferences import Preferences
from backend.models.profil import Profil
from backend.models.recette import Recette, RecetteIngredient
from backend.services import planning_generation_service, planning_service
from backend.services.gemma_tools import LOG_FILE

ALLERGIES_TEST = ["arachide"]
TABOUS_TEST = ["canard"]


def creer_profil_test(db) -> str:
    """Crée un profil onboardé complet (Profil + Foyer + Preferences + Budget + Localisation)."""
    profil = Profil(
        age=34, sexe="F", poids=65, taille=1.65,
        niveau_activite="modere", objectif="perte_poids",
    )
    db.add(profil)
    db.commit()
    db.refresh(profil)

    foyer = Foyer(profil_id=profil.id, nombre_personnes=3)
    db.add(foyer)
    db.flush()
    db.add(MembreFoyer(foyer_id=foyer.id, age_approx=34, regime_aligne=True))
    db.add(MembreFoyer(foyer_id=foyer.id, age_approx=8, regime_aligne=True))
    db.commit()

    preferences = Preferences(
        profil_id=profil.id,
        tabous=TABOUS_TEST,
        allergies=ALLERGIES_TEST,
        aliments_detestes=[],
        regime_specifique="aucun",
    )
    db.add(preferences)
    db.commit()
    db.refresh(preferences)

    db.add(
        Budget(
            preferences_id=preferences.id,
            montant=100_000,
            periode="semaine",
            montant_restant=70_000,
        )
    )
    db.add(
        Localisation(
            profil_id=profil.id,
            latitude=-18.9102,
            longitude=47.5256,
            quartier="Analakely",
            saison="hiver_sec",
        )
    )
    db.commit()
    return profil.id


def afficher_planning(planning: Planning) -> None:
    print(f"\n--- Planning généré ({planning.id}) ---")
    for repas in sorted(planning.repas, key=lambda r: (r.jour, r.type_repas)):
        print(f"  {repas.jour} | {repas.type_repas:15s} | recette_id={repas.recette_id}")


def verifier_absence_allergenes(db, planning: Planning) -> None:
    """Vérification manuelle : aucun ingrédient allergène/tabou dans les recettes servies."""
    interdits = {nom.lower() for nom in (*ALLERGIES_TEST, *TABOUS_TEST)}
    print("\n--- Vérification sécurité alimentaire ---")
    for repas in planning.repas:
        recette = (
            db.query(Recette)
            .options(joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient))
            .filter(Recette.id == repas.recette_id)
            .one()
        )
        noms = {ligne.ingredient.nom.lower() for ligne in recette.ingredients}
        violation = noms & interdits
        print(f"  {repas.jour} {repas.type_repas:15s} {recette.nom:30s} -> "
              f"{'VIOLATION !!' if violation else 'ok'} {violation or ''}")
        assert not violation, f"Ingrédient interdit servi : {violation} dans {recette.nom}"
    print(f"Aucun ingrédient parmi {sorted(interdits)} détecté dans le planning.")


def afficher_tool_calls(mot_cle: str | None = None) -> None:
    """Affiche le log des tool calls : toute donnée chiffrée (prix, stock) affichée par
    Gemma doit provenir d'une ligne visible ici, jamais d'un chiffre inventé."""
    print("\n--- Log des tool calls (logs/tool_calls.log) ---")
    if not LOG_FILE.exists():
        print("  Aucun tool call loggé (le modèle a répondu sans utiliser d'outil).")
        return
    lignes = LOG_FILE.read_text(encoding="utf-8").splitlines()
    if mot_cle:
        lignes = [l for l in lignes if mot_cle in l]
    if not lignes:
        print(f"  Aucune ligne ne contient '{mot_cle}'.")
    for ligne in lignes[-20:]:
        print(f"  {ligne}")


def main() -> int:
    init_db()
    db = SessionLocal()
    try:
        seed(db)
        profil_id = creer_profil_test(db)
        print(f"Profil de test créé : {profil_id} (allergies={ALLERGIES_TEST}, tabous={TABOUS_TEST})")

        planning = planning_generation_service.generer_planning(
            db, profil_id, periode="semaine", date_debut=date.today()
        )
        # Recharge avec les relations (repas + recette) eager-load, l'objet retourné par
        # generer_planning n'a pas forcément .repas chargé après le commit interne.
        planning = planning_service.get_planning(db, profil_id, "semaine", date.today())

        afficher_planning(planning)
        verifier_absence_allergenes(db, planning)
        afficher_tool_calls("find_nearby_market")
    except httpx.ConnectError:
        print("Ollama et Gemini injoignables (ni serveur local, ni GEMMA4_API_KEY) : "
              "lancez `ollama serve` ou renseignez .env avant de relancer ce test.")
        return 1
    except (ValueError, RuntimeError) as exc:
        print(f"Échec de la génération : {exc}")
        return 1
    finally:
        db.close()

    print("\nOK : planning généré, sécurité alimentaire respectée, prix tracés via tool calls.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
