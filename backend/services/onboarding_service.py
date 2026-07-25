from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.budget import Budget
from backend.models.etat_du_jour import EtatDuJour
from backend.models.foyer import Foyer, MembreFoyer
from backend.models.localisation import Localisation
from backend.models.preferences import Preferences
from backend.models.profil import Profil
from backend.schemas.budget import BudgetCreate
from backend.schemas.etat_du_jour import EtatDuJourCreate
from backend.schemas.foyer import FoyerCreate
from backend.schemas.localisation import LocalisationCreate
from backend.schemas.preferences import PreferencesCreate
from backend.schemas.profil import ProfilCreate

FACTEUR_ACTIVITE = {
    "sedentaire": 1.2,
    "leger": 1.375,
    "modere": 1.55,
    "actif": 1.725,
    "tres_actif": 1.9,
}


def calculer_imc(poids: float, taille_cm: float) -> float:
    taille_m = taille_cm / 100.0
    if taille_m <= 0:
        raise HTTPException(status_code=400, detail="Taille invalide pour le calcul d'IMC")
    return round(poids / (taille_m**2), 2)


def calculer_besoin_calorique(
    age: int,
    sexe: str,
    poids: float,
    taille_cm: float,
    niveau_activite: str,
) -> float:
    """Mifflin-St Jeor pondérée par le niveau d'activité."""
    if sexe.lower() in {"homme", "male", "m", "h"}:
        bmr = 10 * poids + 6.25 * taille_cm - 5 * age + 5
    else:
        bmr = 10 * poids + 6.25 * taille_cm - 5 * age - 161

    facteur = FACTEUR_ACTIVITE.get(niveau_activite)
    if facteur is None:
        raise HTTPException(status_code=400, detail=f"Niveau d'activité inconnu: {niveau_activite}")
    return round(bmr * facteur, 1)


def _profil_or_404(db: Session, profil_id: str) -> Profil:
    profil = db.get(Profil, profil_id)
    if not profil:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return profil


def create_profil(db: Session, data: ProfilCreate) -> Profil:
    profil = Profil(**data.model_dump())
    db.add(profil)
    db.commit()
    db.refresh(profil)
    return profil


def get_profil(db: Session, profil_id: str) -> Profil:
    return _profil_or_404(db, profil_id)


def enrich_profil_out(profil: Profil) -> dict:
    return {
        "id": profil.id,
        "age": profil.age,
        "sexe": profil.sexe,
        "poids": profil.poids,
        "taille": profil.taille,
        "niveau_activite": profil.niveau_activite,
        "objectif": profil.objectif,
        "condition_sante": profil.condition_sante,
        "imc": calculer_imc(profil.poids, profil.taille),
        "besoin_calorique": calculer_besoin_calorique(
            profil.age,
            profil.sexe,
            profil.poids,
            profil.taille,
            profil.niveau_activite,
        ),
    }


def create_foyer(db: Session, profil_id: str, data: FoyerCreate) -> Foyer:
    _profil_or_404(db, profil_id)
    existing = db.query(Foyer).filter(Foyer.profil_id == profil_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Un foyer existe déjà pour ce profil")

    foyer = Foyer(profil_id=profil_id, nombre_personnes=data.nombre_personnes)
    db.add(foyer)
    db.flush()

    for membre_data in data.membres:
        db.add(MembreFoyer(foyer_id=foyer.id, **membre_data.model_dump()))

    db.commit()
    return (
        db.query(Foyer)
        .options(joinedload(Foyer.membres))
        .filter(Foyer.id == foyer.id)
        .one()
    )


def get_foyer_by_profil(db: Session, profil_id: str) -> Foyer:
    foyer = (
        db.query(Foyer)
        .options(joinedload(Foyer.membres))
        .filter(Foyer.profil_id == profil_id)
        .first()
    )
    if not foyer:
        raise HTTPException(status_code=404, detail="Foyer introuvable pour ce profil")
    return foyer


def create_preferences(db: Session, profil_id: str, data: PreferencesCreate) -> Preferences:
    _profil_or_404(db, profil_id)
    existing = db.query(Preferences).filter(Preferences.profil_id == profil_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Des préférences existent déjà pour ce profil")

    preferences = Preferences(profil_id=profil_id, **data.model_dump())
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences


def create_budget(db: Session, profil_id: str, data: BudgetCreate) -> Budget:
    preferences = db.query(Preferences).filter(Preferences.profil_id == profil_id).first()
    if not preferences:
        raise HTTPException(
            status_code=404,
            detail="Préférences introuvables — créez-les avant le budget",
        )
    if db.query(Budget).filter(Budget.preferences_id == preferences.id).first():
        raise HTTPException(status_code=409, detail="Un budget existe déjà pour ce profil")

    montant_restant = (
        data.montant_restant if data.montant_restant is not None else data.montant
    )
    budget = Budget(
        preferences_id=preferences.id,
        montant=data.montant,
        periode=data.periode,
        montant_restant=montant_restant,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_budget_by_profil(db: Session, profil_id: str) -> Budget:
    budget = (
        db.query(Budget)
        .join(Preferences)
        .filter(Preferences.profil_id == profil_id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Budget introuvable pour ce profil")
    return budget


def create_localisation(db: Session, profil_id: str, data: LocalisationCreate) -> Localisation:
    _profil_or_404(db, profil_id)
    existing = db.query(Localisation).filter(Localisation.profil_id == profil_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Une localisation existe déjà pour ce profil")

    localisation = Localisation(profil_id=profil_id, **data.model_dump())
    db.add(localisation)
    db.commit()
    db.refresh(localisation)
    return localisation


def create_etat_du_jour(db: Session, profil_id: str, data: EtatDuJourCreate) -> EtatDuJour:
    foyer = db.query(Foyer).filter(Foyer.profil_id == profil_id).first()
    if not foyer:
        raise HTTPException(status_code=404, detail="Foyer introuvable pour ce profil")

    existing = (
        db.query(EtatDuJour)
        .filter(EtatDuJour.foyer_id == foyer.id, EtatDuJour.date == data.date)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Un état du jour existe déjà pour cette date")

    etat = EtatDuJour(foyer_id=foyer.id, **data.model_dump())
    db.add(etat)
    db.commit()
    db.refresh(etat)
    return etat
