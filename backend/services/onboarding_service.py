from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.foyer import Foyer, MembreFoyer
from backend.models.preferences import Preferences
from backend.models.profil import Profil
from backend.models.utilisateur import Utilisateur
from backend.schemas.foyer import FoyerCreate
from backend.schemas.preferences import PreferencesCreate
from backend.schemas.profil import ProfilCreate, ProfilOut
from backend.services.nutrition import calculer_besoin_calorique, calculer_imc


def _profil_or_404(db: Session, profil_id: str) -> Profil:
    profil = db.get(Profil, profil_id)
    if not profil:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return profil


def _age_depuis_naissance(date_naissance: date) -> int:
    today = date.today()
    return today.year - date_naissance.year - (
        (today.month, today.day) < (date_naissance.month, date_naissance.day)
    )


def create_profil(db: Session, data: ProfilCreate) -> Profil:
    utilisateur = db.get(Utilisateur, data.utilisateur_id)
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if db.query(Profil).filter(Profil.utilisateur_id == data.utilisateur_id).first():
        raise HTTPException(
            status_code=409, detail="Un profil existe déjà pour cet utilisateur"
        )

    age = data.age if data.age is not None else _age_depuis_naissance(utilisateur.date_naissance)
    if age < 1 or age > 120:
        raise HTTPException(status_code=400, detail="Âge calculé invalide")

    profil = Profil(
        utilisateur_id=data.utilisateur_id,
        age=age,
        sexe=data.sexe,
        poids=data.poids,
        taille=data.taille,
        niveau_activite=data.niveau_activite,
        objectif=data.objectif,
        condition_sante=data.condition_sante,
    )
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

    # Le profil principal n'est pas dans membres → total >= membres + 1
    if data.nombre_personnes < len(data.membres) + 1:
        raise HTTPException(
            status_code=400,
            detail="nombre_personnes doit être >= nombre de membres + 1 (profil principal)",
        )

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
