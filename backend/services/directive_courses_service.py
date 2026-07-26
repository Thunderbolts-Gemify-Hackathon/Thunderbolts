"""Directive courses structurée pour lecture vocale (données seed KaliTao only)."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.ingredient import Ingredient
from backend.models.localisation import Localisation
from backend.schemas.gemma import DirectiveCoursesResponse
from backend.services.market_service import find_nearby_market


def _resolve_ingredient(
    db: Session,
    *,
    ingredient_id: str | None,
    ingredient_nom: str | None,
) -> Ingredient:
    if ingredient_id:
        ingredient = db.get(Ingredient, ingredient_id)
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient introuvable")
        return ingredient

    nom = (ingredient_nom or "").strip().lower()
    ingredient = (
        db.query(Ingredient)
        .filter(Ingredient.nom.ilike(nom))
        .first()
    )
    if not ingredient:
        raise HTTPException(
            status_code=404, detail=f"Ingredient introuvable: {ingredient_nom}"
        )
    return ingredient


def _pick_best(matches):
    for match in matches:
        if not match.deprioritise:
            return match
    return matches[0]


def build_directive_courses(
    db: Session,
    profil_id: str,
    *,
    ingredient_id: str | None = None,
    ingredient_nom: str | None = None,
    rayon_km: float = 15,
) -> DirectiveCoursesResponse:
    ingredient = _resolve_ingredient(
        db, ingredient_id=ingredient_id, ingredient_nom=ingredient_nom
    )
    loc = db.query(Localisation).filter(Localisation.profil_id == profil_id).first()
    if not loc:
        raise HTTPException(
            status_code=404,
            detail="Localisation manquante. Complete l'onboarding quartier.",
        )

    matches = find_nearby_market(
        db,
        ingredient.id,
        loc.latitude,
        loc.longitude,
        rayon_km=rayon_km,
        profil_id=profil_id,
    )
    if not matches:
        raise HTTPException(
            status_code=404,
            detail="Aucun point de vente dans le rayon pour cet ingredient",
        )

    match = _pick_best(matches)
    itin = match.itineraire
    distance = itin.distance if itin else None
    securite = itin.niveau_securite if itin else None
    mode = itin.mode_deplacement if itin else None
    prix = int(round(match.prix))

    parts = [
        f"Pour {ingredient.nom}, va a {match.point_de_vente.nom}.",
        f"Prix indicatif {prix} Ar.",
    ]
    if distance is not None:
        parts.append(f"Environ {distance} km.")
    if securite == "a_eviter":
        parts.append("Attention, trajet a eviter si possible.")
    elif securite == "prudence":
        parts.append("Trajet a faire avec prudence.")
    elif securite:
        parts.append("Trajet sur.")
    if mode:
        parts.append(f"De preference en {mode}.")

    return DirectiveCoursesResponse(
        ingredient_id=ingredient.id,
        ingredient_nom=ingredient.nom,
        point_de_vente=match.point_de_vente.nom,
        type_pdv=match.point_de_vente.type,
        prix=float(prix),
        distance_km=distance,
        niveau_securite=securite,
        mode_deplacement=mode,
        deprioritise=match.deprioritise,
        phrase=" ".join(parts),
    )
