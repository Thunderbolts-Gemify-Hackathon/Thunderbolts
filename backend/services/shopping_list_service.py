"""Liste de courses par période — quantités/prix calculés de façon déterministe
(jamais par Gemma, pour ne jamais halluciner un chiffre). Gemma est seulement
utilisé pour reformuler la liste en message naturel (`phraser_liste_via_gemma`).

Ancrage : le planning `semaine` déjà généré par Gemma. Pour `mois`, on répète
le pattern hebdomadaire (4× + jours restants) sans régénérer via IA.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session, joinedload

from backend.models.ingredient import Ingredient
from backend.models.localisation import Localisation
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.schemas.point_de_vente import PointDeVenteOut
from backend.services.gemma_client import GemmaClient
from backend.services.market_service import find_nearby_market
from backend.services.stock_service import get_stock_profil

JOURS_PAR_PERIODE = {"jour": 1, "semaine": 7, "mois": 30}


def generer_liste_courses_periode(
    db: Session,
    profil_id: str,
    periode: str,
    date_debut: date,
) -> list[dict[str, Any]]:
    if periode not in JOURS_PAR_PERIODE:
        raise ValueError(f"periode invalide: {periode} (jour|semaine|mois)")

    nb_jours = JOURS_PAR_PERIODE[periode]
    repas = _repas_couvrant_periode(db, profil_id, periode, date_debut, nb_jours)

    requis: dict[str, float] = defaultdict(float)
    unite_par_ingredient: dict[str, str] = {}
    ingredients_map: dict[str, Ingredient] = {}

    for repas_item in repas:
        recette = repas_item["recette"]
        for ligne in recette.ingredients:
            requis[ligne.ingredient_id] += float(ligne.poids_requis)
            unite_par_ingredient[ligne.ingredient_id] = ligne.unite
            ingredients_map[ligne.ingredient_id] = ligne.ingredient

    stock_dispo = {
        ligne.ingredient_id: float(ligne.quantite_disponible)
        for ligne in get_stock_profil(db, profil_id)
    }

    items: list[dict[str, Any]] = []
    for ingredient_id, qte_requise in sorted(
        requis.items(), key=lambda pair: ingredients_map[pair[0]].nom
    ):
        ingredient = ingredients_map[ingredient_id]
        disponible = stock_dispo.get(ingredient_id, 0.0)
        a_acheter = max(0.0, qte_requise - disponible)
        items.append(
            {
                "ingredient": ingredient,
                "categorie": ingredient.categorie or "autre",
                "quantite_totale_requise": round(qte_requise, 2),
                "quantite_disponible": round(disponible, 2),
                "quantite_a_acheter": round(a_acheter, 2),
                "unite": unite_par_ingredient.get(ingredient_id, ingredient.unite_defaut),
                "statut": "disponible" if a_acheter <= 0 else "à acheter",
            }
        )
    return items


def estimer_cout_liste(
    db: Session,
    liste_courses: list[dict[str, Any]],
    lat: float,
    lon: float,
    *,
    profil_id: str | None = None,
    rayon_km: float = 10.0,
) -> dict[str, Any]:
    """Estime le coût via Offre marché (meilleur prix/sécurité), sinon prix_moyen_reference.

    Convention prix : Ar / kg pour g, Ar / L pour ml, Ar / unité sinon.
    """
    details: list[dict[str, Any]] = []
    marches: dict[str, PointDeVenteOut] = {}
    cout_total = 0.0

    for item in liste_courses:
        qte = float(item["quantite_a_acheter"])
        if qte <= 0:
            continue

        ingredient: Ingredient = item["ingredient"]
        unite = item.get("unite") or ingredient.unite_defaut
        match = _meilleure_offre(db, ingredient.id, lat, lon, profil_id, rayon_km)

        if match is not None:
            prix_unitaire = float(match.prix)
            source = "offre"
            pdv = match.point_de_vente
            marches[pdv.id] = pdv
        elif ingredient.prix_moyen_reference is not None:
            prix_unitaire = float(ingredient.prix_moyen_reference)
            source = "reference"
            pdv = None
        else:
            continue

        cout = round(_cout_depuis_prix_unitaire(prix_unitaire, qte, unite), 2)
        cout_total += cout
        details.append(
            {
                "ingredient_id": ingredient.id,
                "ingredient_nom": ingredient.nom,
                "quantite_a_acheter": qte,
                "unite": unite,
                "prix_unitaire": prix_unitaire,
                "cout_estime": cout,
                "source_prix": source,
                "point_de_vente": pdv,
            }
        )

    return {
        "cout_total_estime": round(cout_total, 2),
        "details_par_ingredient": details,
        "marches_a_visiter": list(marches.values()),
    }


def phraser_liste_via_gemma(items: list[dict[str, Any]], periode: str) -> str:
    """Reformule la liste (déjà calculée) en message court. Gemma ne peut ni changer
    les quantités ni ajouter d'ingrédient — on ne lui donne que ce qui est à acheter."""
    a_acheter = [i for i in items if i["quantite_a_acheter"] > 0]
    if not a_acheter:
        return "Rien a acheter, ton stock couvre deja tes repas prevus."

    resume = "\n".join(
        f"{i['ingredient'].nom} : {i['quantite_a_acheter']} {i['unite']} ({i['categorie']})"
        for i in a_acheter
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Tu rediges une liste de courses courte et amicale en francais pour "
                "Sakafo AI, uniquement a partir des quantites deja calculees ci-dessous. "
                "Ne change aucune quantite, n'ajoute et n'invente aucun ingredient hors "
                "de cette liste."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Periode : {periode}. Ingredients a acheter (quantite exacte) :\n{resume}"
                "\n\nRedige un court message (3-5 phrases) qui organise cette liste par "
                "categorie ou priorite, ton naturel et motivant."
            ),
        },
    ]
    try:
        result = GemmaClient().chat(messages)
    except RuntimeError:
        return _message_par_defaut_liste(a_acheter)

    contenu = (result["message"].get("content") or "").strip()
    return contenu or _message_par_defaut_liste(a_acheter)


def _message_par_defaut_liste(a_acheter: list[dict[str, Any]]) -> str:
    noms = ", ".join(i["ingredient"].nom for i in a_acheter[:8])
    suffixe = "…" if len(a_acheter) > 8 else ""
    return f"{len(a_acheter)} ingredient(s) a acheter : {noms}{suffixe}."


def localisation_profil(db: Session, profil_id: str) -> Localisation | None:
    return db.query(Localisation).filter(Localisation.profil_id == profil_id).first()


def _repas_couvrant_periode(
    db: Session,
    profil_id: str,
    periode: str,
    date_debut: date,
    nb_jours: int,
) -> list[dict[str, Any]]:
    """Matérialise les repas de la période sans appeler Gemma.

    - jour / semaine : filtre le planning semaine ancré sur date_debut
    - mois : répète le pattern hebdo sur 30 jours
    """
    planning = _charger_planning_semaine(db, profil_id, date_debut)
    actifs = [r for r in planning.repas if r.statut != "annule"]

    if periode == "jour":
        return [
            {"jour": r.jour, "recette": r.recette, "type_repas": r.type_repas}
            for r in actifs
            if r.jour == date_debut
        ]

    if periode == "semaine":
        return [
            {"jour": r.jour, "recette": r.recette, "type_repas": r.type_repas}
            for r in actifs
        ]

    return _etendre_pattern_hebdo(planning, date_debut, nb_jours)


def _charger_planning_semaine(
    db: Session, profil_id: str, date_debut: date
) -> Planning:
    planning = (
        db.query(Planning)
        .options(
            joinedload(Planning.repas)
            .joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient)
        )
        .filter(
            Planning.profil_id == profil_id,
            Planning.periode == "semaine",
            Planning.date_debut == date_debut,
        )
        .first()
    )
    if planning is not None:
        return planning

    # Fallback : planning semaine dont la fenêtre couvre date_debut
    candidats = (
        db.query(Planning)
        .options(
            joinedload(Planning.repas)
            .joinedload(RepasPlanifie.recette)
            .joinedload(Recette.ingredients)
            .joinedload(RecetteIngredient.ingredient)
        )
        .filter(Planning.profil_id == profil_id, Planning.periode == "semaine")
        .order_by(Planning.date_debut.desc())
        .all()
    )
    for candidat in candidats:
        fin = candidat.date_debut + timedelta(days=6)
        if candidat.date_debut <= date_debut <= fin:
            return candidat

    raise ValueError(
        "Aucun planning semaine trouvé pour cette date. "
        "Générez-le d'abord via POST /ia/{profil_id}/generer-planning."
    )


def _etendre_pattern_hebdo(
    planning: Planning,
    date_debut: date,
    nb_jours: int,
) -> list[dict[str, Any]]:
    """Répète le pattern des 7 jours du planning semaine sur nb_jours (ex. 30)."""
    by_offset: dict[int, list[RepasPlanifie]] = defaultdict(list)
    for repas in planning.repas:
        if repas.statut == "annule":
            continue
        offset = (repas.jour - planning.date_debut).days % 7
        by_offset[offset].append(repas)

    etendus: list[dict[str, Any]] = []
    for day_i in range(nb_jours):
        jour = date_debut + timedelta(days=day_i)
        for template in by_offset.get(day_i % 7, []):
            etendus.append(
                {
                    "jour": jour,
                    "recette": template.recette,
                    "type_repas": template.type_repas,
                }
            )
    return etendus


def _meilleure_offre(
    db: Session,
    ingredient_id: str,
    lat: float,
    lon: float,
    profil_id: str | None,
    rayon_km: float,
):
    matches = find_nearby_market(
        db, ingredient_id, lat, lon, rayon_km=rayon_km, profil_id=profil_id
    )
    if not matches:
        return None
    # find_nearby_market trie déjà (sécurité puis prix)
    return matches[0]


def _cout_depuis_prix_unitaire(prix_unitaire: float, quantite: float, unite: str) -> float:
    if unite in {"g", "ml"}:
        return prix_unitaire * (quantite / 1000.0)
    if unite in {"kg", "l"}:
        return prix_unitaire * quantite
    return prix_unitaire * quantite
