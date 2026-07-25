from datetime import date

from sqlalchemy.orm import Session

from backend.data.catalog import ITINERAIRES, POINTS_DE_VENTE, PRIX_BASE, PRIX_MULT
from backend.data.seed_helpers import get_or_create
from backend.models.itineraire import Itineraire
from backend.models.point_de_vente import Offre, PointDeVente


def seed_markets(db: Session, ingredients: dict) -> None:
    today = date.today()
    pdvs = {}
    for idx, (nom, type_, lat, lon, horaires) in enumerate(POINTS_DE_VENTE):
        pdv = get_or_create(
            db,
            PointDeVente,
            {"nom": nom},
            type=type_,
            latitude=lat,
            longitude=lon,
            horaires_verifies=horaires,
        )
        pdvs[nom] = pdv
        if not pdv.offres:
            mult = PRIX_MULT[idx]
            for ing_nom, base in PRIX_BASE.items():
                db.add(
                    Offre(
                        point_de_vente_id=pdv.id,
                        ingredient_id=ingredients[ing_nom].id,
                        prix=round(base * mult),
                        derniere_mise_a_jour=today,
                    )
                )

    for pdv_nom, distance, securite, mode in ITINERAIRES:
        pdv = pdvs[pdv_nom]
        exists = (
            db.query(Itineraire)
            .filter_by(point_de_vente_id=pdv.id, niveau_securite=securite, profil_id=None)
            .first()
        )
        if not exists:
            db.add(
                Itineraire(
                    point_de_vente_id=pdv.id,
                    distance=distance,
                    niveau_securite=securite,
                    mode_deplacement=mode,
                )
            )
