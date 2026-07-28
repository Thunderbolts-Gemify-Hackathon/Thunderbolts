from __future__ import annotations

from sqlalchemy.orm import Session

from backend.data.food_catalog import INGREDIENTS
from backend.models.ingredient import Ingredient
from backend.services.market_service import find_nearby_market
from backend.services.shopping_list_service import _cout_depuis_prix_unitaire


def check_panier(
    db: Session,
    items: list[dict],
    budget: float,
    *,
    quartier: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    profil_id: str | None = None,
) -> dict:
    """Estime le panier. Si lat/lon fournis : prix via Offres marché, sinon référence."""
    _ = quartier  # utilisé côté client pour contexte ; prix offres via lat/lon
    cout = 0.0
    detail = []
    for raw in items:
        nom = str(raw.get("ingredient_nom") or "").strip().lower()
        qty = float(raw.get("quantite") or 0)
        unite = str(raw.get("unite") or "g").lower()
        iid = raw.get("ingredient_id")
        ing = None
        if iid:
            ing = db.query(Ingredient).filter(Ingredient.id == iid).first()
        if ing is None and nom:
            ing = db.query(Ingredient).filter(Ingredient.nom.ilike(nom)).first()

        prix_ref = None
        source = "reference"
        if ing and lat is not None and lon is not None:
            matches = find_nearby_market(
                db,
                ingredient_id=ing.id,
                lat=lat,
                lon=lon,
                rayon_km=15,
                profil_id=profil_id,
            )
            if matches:
                prix_ref = float(matches[0].prix)
                source = "offre"
        if prix_ref is None and ing and ing.prix_moyen_reference is not None:
            prix_ref = float(ing.prix_moyen_reference)
        elif prix_ref is None and nom in INGREDIENTS:
            prix_ref = float(INGREDIENTS[nom].get("prix_moyen_reference") or 0)
        elif prix_ref is None:
            prix_ref = 2000.0

        line = _cout_depuis_prix_unitaire(prix_ref, qty, unite)
        cout += line
        detail.append(
            {
                "nom": ing.nom if ing else nom,
                "cout": line,
                "prix_ref": prix_ref,
                "source": source,
            }
        )

    ecart = budget - cout
    if ecart >= 0:
        statut = "sous_budget" if ecart > budget * 0.05 else "au_budget"
    else:
        statut = "over_budget"

    swaps = []
    if statut == "over_budget":
        for d in sorted(detail, key=lambda x: -x["cout"])[:3]:
            n = (d["nom"] or "").lower()
            if n in ("poulet", "canard", "poisson"):
                swaps.append(
                    {
                        "ingredient_nom": n,
                        "alternative": "haricot",
                        "economie_estimee": round(d["cout"] * 0.4, 0),
                        "raison": "Protéine végétale moins chère, typique étudiant.",
                    }
                )
            elif n in ("huile",):
                swaps.append(
                    {
                        "ingredient_nom": n,
                        "alternative": "réduire quantité",
                        "economie_estimee": round(d["cout"] * 0.3, 0),
                        "raison": "Réduire l'huile de 30% suffit souvent.",
                    }
                )

    return {
        "cout_estime": round(cout, 0),
        "budget": budget,
        "ecart": round(ecart, 0),
        "statut": statut,
        "swaps": swaps,
    }
