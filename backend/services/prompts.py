"""Prompts système et utilisateur pour l'assistant culinaire Sakafo AI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, TypeVar

from pydantic import BaseModel

from backend.schemas.budget import BudgetOut
from backend.schemas.foyer import FoyerOut
from backend.schemas.localisation import LocalisationOut
from backend.schemas.preferences import PreferencesOut
from backend.schemas.profil import ProfilOut

ModelT = TypeVar("ModelT", bound=BaseModel)

NIVEAUX_ACTIVITE = {
    "sedentaire": "sédentaire",
    "leger": "léger",
    "modere": "modéré",
    "actif": "actif",
    "tres_actif": "très actif",
}

OBJECTIFS = {
    "perte_poids": "perte de poids",
    "maintien": "maintien du poids",
    "prise_masse": "prise de masse",
}

PLANNING_JSON_SHAPE = (
    '[{"jour": "AAAA-MM-JJ", "type_repas": "petit_dejeuner|dejeuner|diner", '
    '"recette_id": "..."}]'
)

RULE_OWN_DATA = (
    "RÈGLE STRICTE — SOURCES AUTORISÉES : tu t'appuies uniquement sur (1) le profil foyer "
    "ci-dessus, (2) les recettes déjà filtrées / fournies par KaliTao, (3) les résultats des "
    "outils backend. Tu n'inventes pas de plats, marchés, prix ou conseils issus du web ou "
    "de connaissances externes non vérifiées par un outil."
)

RULE_NO_HALLUCINATION = (
    "RÈGLE STRICTE — DONNÉES CHIFFRÉES : tu ne dois jamais halluciner un prix, un stock, "
    "une distance ou toute autre donnée chiffrée. Utilise systématiquement les outils "
    "fournis (check_budget, find_nearby_market, find_nearest_supermarkets, check_expiry, "
    "update_stock) pour obtenir ces informations avant de répondre. Utilise "
    "find_nearby_market quand un ingrédient précis est demandé, et "
    "find_nearest_supermarkets quand la demande est générale (\"le marché le plus proche\", "
    "\"comment y aller\") sans produit précis."
)

RULE_FOOD_SAFETY = (
    "RÈGLE STRICTE — SÉCURITÉ ALIMENTAIRE : tu ne dois JAMAIS proposer un ingrédient présent "
    "dans les allergies ou les tabous du profil ci-dessus, sans aucune exception, même si "
    "l'utilisateur le demande explicitement. Si une demande de l'utilisateur entre en conflit "
    "avec une allergie ou un tabou, refuse poliment et propose une alternative sûre."
)

RULE_VOICE_DIRECTIVE = (
    "Quand l'utilisateur demande où acheter un produit, réponds en directive courte et claire "
    "(lieu, prix issu de l'outil, distance, sécurité du trajet). Si un trajet est marqué "
    "a_eviter, propose un autre point de vente."
)

OUTPUT_FORMAT = (
    "FORMAT DE SORTIE : pour un planning de repas, réponds avec un JSON structuré (jours, "
    "repas, ingrédients, quantités). Pour toute explication, recommandation ou échange "
    "conversationnel, réponds en texte naturel en français."
)

RULE_VOICE_MODE = (
    "MODE VOCAL ACTIF : ta réponse va être lue à voix haute, l'utilisateur ne voit pas "
    "de texte. Parle de façon naturelle, chaleureuse et assez développée (2 à 5 phrases), "
    "comme dans une vraie conversation orale — pas de listes à puces, pas de markdown, pas "
    "d'abréviations. Si tu donnes un itinéraire ou une adresse, décris-le pas à pas comme "
    "tu le ferais à voix haute à quelqu'un dans la rue. Termine souvent par une question "
    "ou une proposition pour relancer la conversation."
)

CORRECTION_JSON = (
    "Le format de ta réponse précédente est invalide. Corrige et renvoie UNIQUEMENT un "
    f"tableau JSON de la forme {PLANNING_JSON_SHAPE}, sans texte ni markdown autour."
)


@dataclass(frozen=True)
class PromptContext:
    profil: ProfilOut
    foyer: FoyerOut | None
    preferences: PreferencesOut | None
    budget: BudgetOut | None
    localisation: LocalisationOut | None

    @classmethod
    def from_complet(cls, profil_complet: dict[str, Any]) -> PromptContext:
        return cls(
            profil=ProfilOut.model_validate(profil_complet["profil"]),
            foyer=_parse_optional(FoyerOut, profil_complet.get("foyer")),
            preferences=_parse_optional(PreferencesOut, profil_complet.get("preferences")),
            budget=_parse_optional(BudgetOut, profil_complet.get("budget")),
            localisation=_parse_optional(LocalisationOut, profil_complet.get("localisation")),
        )


def build_system_prompt(profil_complet: dict[str, Any], *, voice: bool = False) -> str:
    """Prompt système à partir du JSON GET /onboarding/{id}/complet.

    `voice=True` (assistant vocal) ajoute une consigne de style parlé — la réponse
    est destinée à être lue à voix haute plutôt que lue à l'écran.
    """
    ctx = PromptContext.from_complet(profil_complet)
    nombre = ctx.foyer.nombre_personnes if ctx.foyer else 1
    parts = [
        (
            f"Tu es l'assistant culinaire de Sakafo AI pour un foyer de {nombre} "
            "personne(s) à Madagascar. Ton rôle est de proposer des repas équilibrés, "
            "réalistes et adaptés aux ressources disponibles du foyer."
        ),
        _describe_profil(ctx.profil),
        _describe_foyer(ctx.foyer),
        _describe_preferences(ctx.preferences),
        _describe_budget(ctx.budget),
        _describe_localisation(ctx.localisation),
        RULE_OWN_DATA,
        RULE_NO_HALLUCINATION,
        RULE_FOOD_SAFETY,
        RULE_VOICE_DIRECTIVE,
        OUTPUT_FORMAT,
    ]
    if voice:
        parts.append(RULE_VOICE_MODE)
    return "\n\n".join(parts)


def build_planning_user_prompt(
    nb_jours: int,
    date_debut: date,
    candidats: list[dict[str, Any]],
) -> str:
    recettes_json = json.dumps(
        [
            {
                "recette_id": r["id"],
                "nom": r["nom"],
                "tags": r["tags"],
                "kcal_total": r["kcal_total"],
                "couverture_stock": round(float(r.get("_couverture", 0.0)), 2),
                "ingredients_manquants": list(r.get("_manquants") or []),
            }
            for r in candidats
        ],
        ensure_ascii=False,
    )
    return (
        f"Génère un planning de repas pour {nb_jours} jours à partir du {date_debut.isoformat()}, "
        "un repas par créneau (petit_dejeuner, dejeuner, diner) et par jour. "
        "Privilégie les recettes avec une couverture_stock élevée et peu "
        "d'ingredients_manquants — utilise EXACTEMENT ces champs pour savoir ce qui "
        "manque en stock, n'invente jamais un ingrédient manquant qui n'y figure pas. "
        f"Choisis UNIQUEMENT parmi ces recettes (n'invente jamais de recette_id) : {recettes_json}\n\n"
        f"Réponds UNIQUEMENT avec un tableau JSON de la forme {PLANNING_JSON_SHAPE}, "
        "sans texte ni markdown autour."
    )


def build_etapes_system_prompt() -> str:
    return (
        "Tu es Kaly Tao, assistant culinaire. Réponds uniquement en français, "
        "de façon brève, et strictement en JSON valide — sans phrase d'introduction, "
        "sans conclusion, sans markdown, sans appel d'outil."
    )


def build_etapes_user_prompt(nom: str, ingredients: list[str]) -> str:
    liste = ", ".join(ingredients) if ingredients else "aucun ingrédient renseigné"
    return (
        f'Donne les étapes pour préparer "{nom}" en 3 à 5 étapes courtes, dans l\'ordre. '
        "Réponds uniquement avec un tableau JSON (aucun texte autour), au format exact : "
        '[{"titre": "phrase courte à l\'impératif", "ingredients": ["..."]}]. '
        "Le titre de chaque étape doit être une seule phrase courte et actionnable. "
        "Les ingrédients de chaque étape doivent venir uniquement de cette liste "
        f"(n'en invente aucun autre, laisse la liste vide si aucun ne s'applique) : {liste}."
    )


def _parse_optional(model: type[ModelT], data: dict[str, Any] | None) -> ModelT | None:
    return model.model_validate(data) if data else None


def _join_or_aucun(valeurs: list[str]) -> str:
    return ", ".join(valeurs) if valeurs else "aucune"


def _describe_profil(profil: ProfilOut) -> str:
    objectif = OBJECTIFS.get(profil.objectif, profil.objectif)
    niveau = NIVEAUX_ACTIVITE.get(profil.niveau_activite, profil.niveau_activite)
    lignes = [
        f"Profil principal : {profil.age} ans, objectif {objectif}, "
        f"niveau d'activité {niveau}."
    ]
    if profil.besoin_calorique:
        lignes.append(f"Besoin calorique estimé : {profil.besoin_calorique} kcal/jour.")
    if profil.condition_sante:
        lignes.append(f"Condition de santé à prendre en compte : {profil.condition_sante}.")
    return "\n".join(lignes)


def _describe_foyer(foyer: FoyerOut | None) -> str:
    if foyer is None:
        return "Composition du foyer : non renseignée."

    ligne = f"Foyer de {foyer.nombre_personnes} personne(s)."
    membres = ", ".join(_describe_membre(m) for m in foyer.membres)
    return f"{ligne} Membres : {membres}." if membres else ligne


def _describe_membre(membre) -> str:
    parts = []
    if membre.prenom:
        parts.append(membre.prenom)
    if membre.lien:
        parts.append(f"({membre.lien})")
    parts.append(f"{membre.age_approx} ans")
    if not membre.regime_aligne:
        parts.append("(régime différent)")
    return " ".join(parts)


def _describe_preferences(preferences: PreferencesOut | None) -> str:
    if preferences is None:
        return (
            "ALLERGIES STRICTES (ne jamais proposer, sans exception) : aucune.\n"
            "Tabous alimentaires : aucun."
        )

    lignes = [
        "ALLERGIES STRICTES (ne jamais proposer, sans exception) : "
        f"{_join_or_aucun(preferences.allergies)}.",
        f"Tabous alimentaires : {_join_or_aucun(preferences.tabous)}.",
    ]
    if preferences.regime_specifique and preferences.regime_specifique != "aucun":
        lignes.append(f"Régime spécifique à respecter : {preferences.regime_specifique}.")
    if preferences.aliments_aimes:
        lignes.append(
            "Aliments appréciés (à privilégier si possible) : "
            f"{_join_or_aucun(preferences.aliments_aimes)}."
        )
    if preferences.aliments_detestes:
        lignes.append(
            "Aliments à éviter par préférence (non médical) : "
            f"{_join_or_aucun(preferences.aliments_detestes)}."
        )
    return "\n".join(lignes)


def _describe_budget(budget: BudgetOut | None) -> str:
    if budget is None:
        return "Budget disponible : non renseigné."
    devise = budget.devise or "Ar"
    return (
        f"Budget disponible : {budget.montant_restant} {devise} "
        f"restants sur la {budget.periode}."
    )


def _describe_localisation(localisation: LocalisationOut | None) -> str:
    if localisation is None:
        return "Localisation : non renseignée."

    details = ", ".join(
        part
        for part in (
            f"quartier {localisation.quartier}" if localisation.quartier else None,
            f"saison {localisation.saison}" if localisation.saison else None,
        )
        if part
    )
    if details:
        return f"Localisation : {details}."
    return "Localisation : coordonnées connues, quartier non précisé."
