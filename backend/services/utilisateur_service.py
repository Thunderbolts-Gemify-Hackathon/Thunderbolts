import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.utilisateur import Utilisateur
from backend.schemas.utilisateur import UtilisateurCreate, UtilisateurLogin
from backend.services.security import hash_password, verify_password


def create_utilisateur(db: Session, data: UtilisateurCreate) -> Utilisateur:
    if db.query(Utilisateur).filter(Utilisateur.email == data.email).first():
        raise HTTPException(status_code=409, detail="Un utilisateur existe déjà avec cet email")

    utilisateur = Utilisateur(
        nom=data.nom,
        prenom=data.prenom,
        email=data.email,
        date_naissance=data.date_naissance,
        mot_de_passe_hash=hash_password(data.mot_de_passe),
        api_token=uuid.uuid4().hex,
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


def authenticate_utilisateur(db: Session, data: UtilisateurLogin) -> Utilisateur:
    erreur = HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    utilisateur = db.query(Utilisateur).filter(Utilisateur.email == data.email).first()
    if not utilisateur or not verify_password(data.mot_de_passe, utilisateur.mot_de_passe_hash):
        raise erreur
    return utilisateur


def get_utilisateur(db: Session, utilisateur_id: str) -> Utilisateur:
    utilisateur = db.get(Utilisateur, utilisateur_id)
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return utilisateur
