"""Conversion d'unités alimentaires (g/kg, ml/L, unité).

Évite l'incohérence classique : stock « 1 kg » traité comme insuffisant face à
une recette « 200 g » parce qu'on comparait 1 < 200 sans conversion.
"""

from __future__ import annotations

_ALIASES = {
    "gramme": "g",
    "grammes": "g",
    "kilogramme": "kg",
    "kilogrammes": "kg",
    "millilitre": "ml",
    "millilitres": "ml",
    "litre": "l",
    "litres": "l",
    "pièce": "unite",
    "piece": "unite",
    "unités": "unite",
    "unites": "unite",
    "unité": "unite",
}


def normalize_unit(unite: str | None) -> str:
    u = (unite or "").strip().lower()
    return _ALIASES.get(u, u)


def to_base(quantite: float, unite: str | None) -> tuple[float, str]:
    """Convertit vers l'unité de base (g, ml, ou unite)."""
    u = normalize_unit(unite)
    if u == "kg":
        return float(quantite) * 1000.0, "g"
    if u == "l":
        return float(quantite) * 1000.0, "ml"
    return float(quantite), u


def convert_quantity(
    quantite: float,
    from_unite: str | None,
    to_unite: str | None,
) -> float | None:
    """Convertit `quantite` de `from_unite` vers `to_unite`. None si incompatibles."""
    q_base, base_from = to_base(quantite, from_unite)
    _, base_to = to_base(1.0, to_unite)
    if base_from != base_to:
        return None
    target = normalize_unit(to_unite)
    if target == "kg":
        return q_base / 1000.0
    if target == "l":
        return q_base / 1000.0
    return q_base


def quantite_suffisante(
    disponible: float,
    unite_disponible: str | None,
    besoin: float,
    unite_besoin: str | None,
) -> bool:
    dispo_base, base_dispo = to_base(disponible, unite_disponible)
    besoin_base, base_besoin = to_base(besoin, unite_besoin)
    if base_dispo != base_besoin:
        return False
    return dispo_base + 1e-9 >= besoin_base
