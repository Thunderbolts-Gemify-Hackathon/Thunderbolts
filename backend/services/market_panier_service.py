from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.ingredient import Ingredient
from backend.data.food_catalog import INGREDIENTS


def check_panier(
    db: Session,
    items: list[dict],
    budget: float,
    *,
    quartier: str | None = None,
) -> dict:
    cout = 0.0
    detail = []
    for raw in items:
        nom = str(raw.get("ingredient_nom") or "").strip().lower()
        qty = float(raw.get("quantite") or 0)
        unite = str(raw.get("unite") or "g").lower()
        ing = db.query(Ingredient).filter(Ingredient.nom.ilike(nom)).first()
        prix_ref = None
        if ing and ing.prix_moyen_reference is not None:
            prix_ref = float(ing.prix_moyen_reference)
        elif nom in INGREDIENTS:
            prix_ref = float(INGREDIENTS[nom].get("prix_moyen_reference") or 0)
        else:
            prix_ref = 2000.0
        if unite in ("g", "ml"):
            line = prix_ref * (qty / 1000.0)
        elif unite == "kg":
            line = prix_ref * qty
        else:
            line = prix_ref * qty
        cout += line
        detail.append({"nom": nom, "cout": line, "prix_ref": prix_ref})

    ecart = budget - cout
    if ecart >= 0:
        statut = "sous_budget" if ecart > budget * 0.05 else "au_budget"
    else:
        statut = "over_budget"

    swaps = []
    if statut == "over_budget":
        # Suggestions simples : protéines chères → haricot / pois
        for d in sorted(detail, key=lambda x: -x["cout"])[:3]:
            if d["nom"] in ("poulet", "canard", "poisson"):
                swaps.append(
                    {
                        "ingredient_nom": d["nom"],
                        "alternative": "haricot",
                        "economie_estimee": round(d["cout"] * 0.4, 0),
                        "raison": "Protéine végétale moins chère, typique étudiant.",
                    }
                )
            elif d["nom"] in ("huile",):
                swaps.append(
                    {
                        "ingredient_nom": d["nom"],
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
