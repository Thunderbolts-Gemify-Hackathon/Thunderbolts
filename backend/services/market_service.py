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
    """Distance en km entre deux points GPS (formule haversine)."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
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
    """
    Offres pour ingredient_id dans le rayon, triées par prix croissant.
    Un itinéraire "a_eviter" n'est jamais en tête — renvoyé en fin avec deprioritise=True.
    """
    offres = (
        db.query(Offre)
        .options(
            joinedload(Offre.point_de_vente).joinedload(PointDeVente.itineraires)
        )
        .filter(Offre.ingredient_id == ingredient_id)
        .all()
    )

    matches: list[MarketMatchOut] = []
    for offre in offres:
        pdv = offre.point_de_vente
        distance = haversine(lat, lon, pdv.latitude, pdv.longitude)
        if distance > rayon_km:
            continue

        itineraire = _choisir_itineraire(list(pdv.itineraires), profil_id)
        niveau = itineraire.niveau_securite if itineraire else "sur"
        deprioritise = niveau == "a_eviter"

        matches.append(
            MarketMatchOut(
                point_de_vente=PointDeVenteOut.model_validate(pdv),
                prix=offre.prix,
                itineraire=ItineraireOut.model_validate(itineraire) if itineraire else None,
                deprioritise=deprioritise,
            )
        )

    # Tri prix croissant, puis a_eviter en fin de liste
    matches.sort(key=lambda m: (m.deprioritise, m.prix))
    return matches


def get_meilleur_compromis(
    db: Session,
    ingredient_id: str,
    lat: float,
    lon: float,
    profil_id: Optional[str] = None,
) -> MarketMatchOut:
    """
    RF-17 : parmi les 3 moins chers (hors dépriorisation stricte du tri),
    prend le premier qui n'est pas "a_eviter".
    """
    matches = find_nearby_market(
        db, ingredient_id, lat, lon, rayon_km=10, profil_id=profil_id
    )
    if not matches:
        raise HTTPException(
            status_code=404,
            detail="Aucun point de vente trouvé pour cet ingrédient",
        )

    # Remettre temporairement un tri prix pur pour les 3 moins chers
    par_prix = sorted(matches, key=lambda m: m.prix)
    top3 = par_prix[:3]
    for match in top3:
        if not match.deprioritise:
            return match

    # Fallback : premier non a_eviter de la liste triée métier, sinon le moins cher
    for match in matches:
        if not match.deprioritise:
            return match
    return par_prix[0]
