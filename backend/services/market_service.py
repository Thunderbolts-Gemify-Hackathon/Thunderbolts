import math
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.itineraire import Itineraire
from backend.models.point_de_vente import Offre, PointDeVente
from backend.schemas.composites import MarketMatchOut
from backend.schemas.itineraire import ItineraireOut
from backend.schemas.point_de_vente import PointDeVenteOut


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _choisir_itineraire(
    itineraires: list[Itineraire], profil_id: Optional[str] = None
) -> Optional[Itineraire]:
    if not itineraires:
        return None
    if profil_id:
        for it in itineraires:
            if it.profil_id == profil_id:
                return it
    for it in itineraires:
        if it.profil_id is None:
            return it
    return itineraires[0]


def find_nearby_market(
    db: Session,
    ingredient_id: str,
    lat: float,
    lon: float,
    rayon_km: float = 10,
    profil_id: Optional[str] = None,
) -> list[MarketMatchOut]:
    offres = (
        db.query(Offre)
        .options(joinedload(Offre.point_de_vente).joinedload(PointDeVente.itineraires))
        .filter(Offre.ingredient_id == ingredient_id)
        .all()
    )

    matches: list[MarketMatchOut] = []
    for offre in offres:
        pdv = offre.point_de_vente
        if haversine(lat, lon, pdv.latitude, pdv.longitude) > rayon_km:
            continue
        itineraire = _choisir_itineraire(list(pdv.itineraires), profil_id)
        deprioritise = bool(itineraire and itineraire.niveau_securite == "a_eviter")
        matches.append(
            MarketMatchOut(
                point_de_vente=PointDeVenteOut.model_validate(pdv),
                prix=offre.prix,
                itineraire=ItineraireOut.model_validate(itineraire) if itineraire else None,
                deprioritise=deprioritise,
            )
        )

    matches.sort(key=lambda m: (m.deprioritise, m.prix))
    return matches


def get_meilleur_compromis(
    db: Session,
    ingredient_id: str,
    lat: float,
    lon: float,
    profil_id: Optional[str] = None,
) -> MarketMatchOut:
    matches = find_nearby_market(db, ingredient_id, lat, lon, profil_id=profil_id)
    if not matches:
        raise HTTPException(status_code=404, detail="Aucun point de vente trouvé pour cet ingrédient")

    top3 = sorted(matches, key=lambda m: m.prix)[:3]
    for match in top3:
        if not match.deprioritise:
            return match
    for match in matches:
        if not match.deprioritise:
            return match
    return top3[0]
