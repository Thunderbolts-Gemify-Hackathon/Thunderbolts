"""Optimisation « un trajet » : couvrir une liste de courses avec le moins de marchés."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.models.ingredient import Ingredient
from backend.services.market_service import find_nearby_market, haversine
from backend.services.shopping_list_service import _cout_depuis_prix_unitaire


def optimize_one_trip(
    db: Session,
    items: list[dict[str, Any]],
    *,
    lat: float,
    lon: float,
    rayon_km: float = 15.0,
    profil_id: str | None = None,
    budget: float | None = None,
) -> dict[str, Any]:
    """Greedy set-cover : choisit des PDV qui couvrent le plus d'articles restants
    au meilleur rapport prix / distance, jusqu'à couvrir toute la liste.

    `items` : {ingredient_id?} | {ingredient_nom?}, quantite, unite.
    """
    resolved = _resolve_items(db, items)
    if not resolved:
        raise ValueError("Aucun ingrédient valide dans la liste")

    # pdv_id -> { meta, offers: {ingredient_id: match} }
    pdv_index: dict[str, dict[str, Any]] = {}
    uncovered = {r["ingredient_id"] for r in resolved}

    for r in resolved:
        matches = find_nearby_market(
            db,
            ingredient_id=r["ingredient_id"],
            lat=lat,
            lon=lon,
            rayon_km=rayon_km,
            profil_id=profil_id,
        )
        for m in matches:
            pdv = m.point_de_vente
            entry = pdv_index.setdefault(
                pdv.id,
                {
                    "pdv": pdv,
                    "distance_km": haversine(lat, lon, pdv.latitude, pdv.longitude),
                    "offers": {},
                },
            )
            # Garde la meilleure offre (premier = déjà trié sécurité/prix)
            if r["ingredient_id"] not in entry["offers"]:
                entry["offers"][r["ingredient_id"]] = m

    stops: list[dict[str, Any]] = []
    remaining = set(uncovered)
    qty_by_id = {r["ingredient_id"]: r for r in resolved}
    total_cout = 0.0

    while remaining and pdv_index:
        best_id = None
        best_score = None
        for pdv_id, entry in pdv_index.items():
            cover = remaining & set(entry["offers"].keys())
            if not cover:
                continue
            # Score : maximiser couverture, minimiser distance et prix moyen
            prix_sum = 0.0
            for iid in cover:
                m = entry["offers"][iid]
                item = qty_by_id[iid]
                prix_sum += _cout_depuis_prix_unitaire(
                    float(m.prix), item["quantite"], item["unite"]
                )
            dist = float(entry["distance_km"]) or 0.01
            # Plus bas = mieux
            score = (dist / max(len(cover), 1)) + (prix_sum / max(len(cover), 1) / 50000.0)
            score -= len(cover) * 0.5  # bonus couverture
            if best_score is None or score < best_score:
                best_score = score
                best_id = pdv_id

        if best_id is None:
            break

        entry = pdv_index.pop(best_id)
        cover = remaining & set(entry["offers"].keys())
        line_items = []
        stop_cout = 0.0
        for iid in sorted(cover, key=lambda x: qty_by_id[x]["nom"]):
            item = qty_by_id[iid]
            m = entry["offers"][iid]
            cout = round(
                _cout_depuis_prix_unitaire(float(m.prix), item["quantite"], item["unite"]),
                2,
            )
            stop_cout += cout
            line_items.append(
                {
                    "ingredient_id": iid,
                    "ingredient_nom": item["nom"],
                    "quantite": item["quantite"],
                    "unite": item["unite"],
                    "prix_unitaire": float(m.prix),
                    "cout_estime": cout,
                }
            )
            remaining.discard(iid)

        pdv = entry["pdv"]
        total_cout += stop_cout
        stops.append(
            {
                "point_de_vente": {
                    "id": pdv.id,
                    "nom": pdv.nom,
                    "type": pdv.type,
                    "latitude": pdv.latitude,
                    "longitude": pdv.longitude,
                },
                "distance_km": round(float(entry["distance_km"]), 2),
                "cout_estime": round(stop_cout, 2),
                "items": line_items,
            }
        )

    # Tri des arrêts par distance croissante (trajet naturel depuis chez soi)
    stops.sort(key=lambda s: s["distance_km"])

    manquants = [
        {
            "ingredient_id": qty_by_id[iid]["ingredient_id"],
            "ingredient_nom": qty_by_id[iid]["nom"],
            "raison": "Aucune offre dans le rayon",
        }
        for iid in remaining
    ]

    ecart = None
    statut = "ok"
    if budget is not None:
        ecart = round(budget - total_cout, 0)
        if ecart < 0:
            statut = "over_budget"
        elif ecart > budget * 0.05:
            statut = "sous_budget"
        else:
            statut = "au_budget"

    return {
        "nb_arrets": len(stops),
        "distance_totale_km": round(sum(s["distance_km"] for s in stops), 2),
        "cout_estime": round(total_cout, 0),
        "budget": budget,
        "ecart": ecart,
        "statut": statut,
        "stops": stops,
        "manquants": manquants,
        "message": _message(stops, manquants),
    }


def _message(stops: list[dict], manquants: list[dict]) -> str:
    if not stops and manquants:
        return "Aucun marché trouvé dans le rayon pour ces produits."
    if len(stops) == 1:
        nom = stops[0]["point_de_vente"]["nom"]
        msg = f"Un seul arrêt suffit : {nom}."
    else:
        noms = ", ".join(s["point_de_vente"]["nom"] for s in stops)
        msg = f"{len(stops)} arrêts recommandés : {noms}."
    if manquants:
        msg += f" {len(manquants)} produit(s) sans offre proche."
    return msg


def _resolve_items(db: Session, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in items:
        qty = float(raw.get("quantite") or 0)
        if qty <= 0:
            continue
        unite = str(raw.get("unite") or "g")
        ing = None
        iid = raw.get("ingredient_id")
        if iid:
            ing = db.query(Ingredient).filter(Ingredient.id == iid).first()
        if ing is None:
            nom = str(raw.get("ingredient_nom") or "").strip()
            if nom:
                ing = db.query(Ingredient).filter(Ingredient.nom.ilike(nom)).first()
        if ing is None:
            continue
        out.append(
            {
                "ingredient_id": ing.id,
                "nom": ing.nom,
                "quantite": qty,
                "unite": unite,
            }
        )
    return out
