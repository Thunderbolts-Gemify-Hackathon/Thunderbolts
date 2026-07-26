from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.models.depense import Depense
from backend.models.stock import IngredientStock, Stock
from backend.services import stock_alerts


def compute_anti_gaspi(db: Session, profil_id: str) -> dict:
    """Estime les ariary sauvés via stocks consommés avant péremption + streak."""
    alertes = stock_alerts.check_expiry(db, profil_id, jours=3)
    # Heuristique : si on a peu d'alertes urgentes et des dépenses repas récentes,
    # on considère qu'on a sauvé la valeur estimée des items proches.
    items_sauves = 0
    ariary = 0.0
    stock = db.query(Stock).filter(Stock.profil_id == profil_id).first()
    if stock:
        lignes = (
            db.query(IngredientStock)
            .filter(IngredientStock.stock_id == stock.id)
            .all()
        )
        today = date.today()
        for ligne in lignes:
            if not ligne.date_peremption:
                continue
            # Consommé / utilisé : péremption dans 0-7j et quantité encore utile
            delta = (ligne.date_peremption - today).days
            if 0 <= delta <= 7 and ligne.quantite_disponible > 0:
                items_sauves += 1
                prix = 0.0
                if ligne.ingredient and ligne.ingredient.prix_moyen_reference:
                    prix = float(ligne.ingredient.prix_moyen_reference)
                    unite = (ligne.unite or "g").lower()
                    qty = float(ligne.quantite_disponible)
                    if unite in ("g", "ml"):
                        ariary += prix * (qty / 1000.0)
                    else:
                        ariary += prix * qty

    # Streak : jours consécutifs avec au moins une dépense repas
    streak = _streak_jours(db, profil_id)
    # Bonus anti-gaspi si peu d'alertes critiques
    critiques = [a for a in alertes if a.date_peremption and (a.date_peremption - date.today()).days <= 1]
    if not critiques and items_sauves:
        message = f"Bravo : ~{int(ariary)} Ar sauvés, streak {streak} j."
    elif critiques:
        message = f"{len(critiques)} produit(s) à utiliser aujourd'hui."
    else:
        message = "Continue à cuisiner ce qui périme — le compteur va monter."

    return {
        "ariary_sauves": round(ariary, 0),
        "items_sauves": items_sauves,
        "streak_jours": streak,
        "message": message,
    }


def _streak_jours(db: Session, profil_id: str) -> int:
    depenses = (
        db.query(Depense)
        .filter(Depense.profil_id == profil_id, Depense.source == "repas")
        .order_by(Depense.created_at.desc())
        .limit(60)
        .all()
    )
    if not depenses:
        return 0
    jours = {d.created_at.date() for d in depenses if d.created_at}
    streak = 0
    cursor = date.today()
    while cursor in jours:
        streak += 1
        cursor -= timedelta(days=1)
    # Si pas aujourd'hui, compter depuis hier
    if streak == 0:
        cursor = date.today() - timedelta(days=1)
        while cursor in jours:
            streak += 1
            cursor -= timedelta(days=1)
    return streak
