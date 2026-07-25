from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.foyer import Foyer, MembreFoyer
from backend.models.preferences import Preferences
from backend.models.profil import Profil
from backend.schemas.foyer import FoyerCreate
from backend.schemas.preferences import PreferencesCreate
from backend.schemas.profil import ProfilCreate, ProfilOut
from backend.services.nutrition import calculer_besoin_calorique, calculer_imc


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


def enrich_profil_out(profil: Profil) -> ProfilOut:
    out = ProfilOut.model_validate(profil)
    out.imc = calculer_imc(profil.poids, profil.taille)
    out.besoin_calorique = calculer_besoin_calorique(
        profil.age, profil.sexe, profil.poids, profil.taille, profil.niveau_activite
    )
    return out


def create_foyer(db: Session, profil_id: str, data: FoyerCreate) -> Foyer:
    _profil_or_404(db, profil_id)
    if db.query(Foyer).filter(Foyer.profil_id == profil_id).first():
        raise HTTPException(status_code=409, detail="Un foyer existe déjà pour ce profil")

    foyer = Foyer(profil_id=profil_id, nombre_personnes=data.nombre_personnes)
    db.add(foyer)
    db.flush()
    for membre_data in data.membres:
        db.add(MembreFoyer(foyer_id=foyer.id, **membre_data.model_dump()))
    db.commit()
    return (
        db.query(Foyer).options(joinedload(Foyer.membres)).filter(Foyer.id == foyer.id).one()
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
    if db.query(Preferences).filter(Preferences.profil_id == profil_id).first():
        raise HTTPException(status_code=409, detail="Des préférences existent déjà pour ce profil")
    preferences = Preferences(profil_id=profil_id, **data.model_dump())
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences
