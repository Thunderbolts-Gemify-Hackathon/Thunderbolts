import math
from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.itineraire import Itineraire
from backend.models.localisation import Localisation
from backend.models.point_de_vente import Offre, PointDeVente
from backend.models.price_report import PriceIndex
from backend.schemas.composites import MarketMatchOut, PointDeVenteProcheOut
from backend.schemas.itineraire import ItineraireOut
from backend.schemas.point_de_vente import PointDeVenteOut

# Variation de prix par point de vente (même logique que le catalogue démo :
# grandes surfaces un peu plus chères, grossistes/épiceries moins chers).
# Les valeurs de PRIX_BASE (market_catalog) sont des références saisonnières
# approximatives Antananarivo — le crowd PriceIndex affine le ranking local.
_VARIANCE_PRIX = [1.15, 1.25, 1.20, 0.75, 0.85, 0.70, 1.10, 0.90]
_PRIX_DEFAUT_SANS_REFERENCE = 3000.0
_CROWD_TOLERANCE = 0.15  # 15 % autour de la moyenne crowd


def seed_offres_pour_ingredient(db: Session, ingredient: Ingredient) -> int:
    """Un produit ajouté hors catalogue démo (ex. via "Mon stock") n'a par
    définition aucune Offre en base : sans ça, il est introuvable sur la
    carte marchés ("Aucun marché") même si l'utilisateur est au bon endroit.
    On génère ici une offre plausible sur chaque point de vente existant,
    basée sur le prix de référence donné (ou un prix générique sinon), pour
    que le nouveau produit se comporte immédiatement comme les autres."""
    prix_base = ingredient.prix_moyen_reference or _PRIX_DEFAUT_SANS_REFERENCE
    pdvs = db.query(PointDeVente).all()
    if not pdvs:
        return 0

    today = date.today()
    created = 0
    for idx, pdv in enumerate(pdvs):
        exists = (
            db.query(Offre)
            .filter(Offre.point_de_vente_id == pdv.id, Offre.ingredient_id == ingredient.id)
            .first()
        )
        if exists:
            continue
        mult = _VARIANCE_PRIX[idx % len(_VARIANCE_PRIX)]
        db.add(
            Offre(
                point_de_vente_id=pdv.id,
                ingredient_id=ingredient.id,
                prix=round(prix_base * mult),
                derniere_mise_a_jour=today,
            )
        )
        created += 1
    db.commit()
    return created


def backfill_offres_manquantes(db: Session) -> int:
    """Rattrape les produits déjà en base sans aucune offre (ex. ajoutés via
    "Mon stock" avant ce correctif) — appelé au démarrage du backend pour
    qu'aucun produit ne reste invisible sur la carte marchés."""
    ingredients_sans_offre = (
        db.query(Ingredient).filter(~Ingredient.offres.any()).all()
    )
    total = 0
    for ingredient in ingredients_sans_offre:
        total += seed_offres_pour_ingredient(db, ingredient)
    return total


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


def _crowd_prix(
    db: Session, ingredient_id: str, profil_id: Optional[str]
) -> float | None:
    if not profil_id:
        return None
    loc = db.query(Localisation).filter(Localisation.profil_id == profil_id).first()
    if not loc or not loc.quartier:
        return None
    quartier = loc.quartier.strip().lower()
    idx = (
        db.query(PriceIndex)
        .filter(
            PriceIndex.ingredient_id == ingredient_id,
            PriceIndex.quartier == quartier,
        )
        .order_by(PriceIndex.jour.desc())
        .first()
    )
    return float(idx.prix_moyen) if idx else None


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

    crowd = _crowd_prix(db, ingredient_id, profil_id)
    scored: list[tuple[MarketMatchOut, float, float]] = []
    for offre in offres:
        pdv = offre.point_de_vente
        distance = haversine(lat, lon, pdv.latitude, pdv.longitude)
        if distance > rayon_km:
            continue
        itineraire = _choisir_itineraire(list(pdv.itineraires), profil_id)
        deprioritise = bool(itineraire and itineraire.niveau_securite == "a_eviter")
        ecart_pct: float | None = None
        if crowd and crowd > 0:
            ecart_pct = abs(offre.prix - crowd) / crowd
        scored.append(
            (
                MarketMatchOut(
                    point_de_vente=PointDeVenteOut.model_validate(pdv),
                    prix=offre.prix,
                    itineraire=ItineraireOut.model_validate(itineraire) if itineraire else None,
                    deprioritise=deprioritise,
                    prix_crowd=crowd,
                    ecart_crowd_pct=round(ecart_pct * 100, 2) if ecart_pct is not None else None,
                ),
                ecart_pct if ecart_pct is not None else 0.0,
                distance,
            )
        )

    # Préfère les PDV dont le prix est dans ±15 % du crowd ; sinon écart relatif.
    def _sort_key(item: tuple[MarketMatchOut, float, float]) -> tuple:
        match, ecart, distance = item
        hors_bande = 1 if (crowd and ecart > _CROWD_TOLERANCE) else 0
        return (match.deprioritise, hors_bande, ecart, match.prix, distance)

    scored.sort(key=_sort_key)
    return [m for m, _, _ in scored]


def find_nearest_points_de_vente(
    db: Session,
    lat: float,
    lon: float,
    rayon_km: float = 10,
    limit: int = 5,
    type_souhaite: Optional[str] = None,
    profil_id: Optional[str] = None,
) -> list[PointDeVenteProcheOut]:
    """Points de vente les plus proches, sans filtre par ingrédient — pour
    répondre à "trouve-moi le marché/supermarché le plus proche" en général,
    utile pour l'assistant vocal qui n'a pas forcément un produit précis en tête."""
    query = db.query(PointDeVente).options(joinedload(PointDeVente.itineraires))
    if type_souhaite:
        query = query.filter(PointDeVente.type.ilike(type_souhaite.strip()))
    pdvs = query.all()

    matches: list[PointDeVenteProcheOut] = []
    for pdv in pdvs:
        distance = haversine(lat, lon, pdv.latitude, pdv.longitude)
        if distance > rayon_km:
            continue
        itineraire = _choisir_itineraire(list(pdv.itineraires), profil_id)
        deprioritise = bool(itineraire and itineraire.niveau_securite == "a_eviter")
        matches.append(
            PointDeVenteProcheOut(
                point_de_vente=PointDeVenteOut.model_validate(pdv),
                distance_km=round(distance, 1),
                itineraire=ItineraireOut.model_validate(itineraire) if itineraire else None,
                deprioritise=deprioritise,
            )
        )

    matches.sort(key=lambda m: (m.deprioritise, m.distance_km))
    return matches[:limit]


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
