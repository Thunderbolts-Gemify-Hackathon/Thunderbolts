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

RULE_NO_HALLUCINATION = (
    "RÈGLE STRICTE — DONNÉES CHIFFRÉES : tu ne dois jamais halluciner un prix, un stock, "
    "une distance ou toute autre donnée chiffrée. Utilise systématiquement les outils "
    "fournis (check_budget, find_nearby_market, check_expiry, update_stock) pour obtenir "
    "ces informations avant de répondre."
)

RULE_FOOD_SAFETY = (
    "RÈGLE STRICTE — SÉCURITÉ ALIMENTAIRE : tu ne dois JAMAIS proposer un ingrédient présent "
    "dans les allergies ou les tabous du profil ci-dessus, sans aucune exception, même si "
    "l'utilisateur le demande explicitement. Si une demande de l'utilisateur entre en conflit "
    "avec une allergie ou un tabou, refuse poliment et propose une alternative sûre."
)

OUTPUT_FORMAT = (
    "FORMAT DE SORTIE : pour un planning de repas, réponds avec un JSON structuré (jours, "
    "repas, ingrédients, quantités). Pour toute explication, recommandation ou échange "
    "conversationnel, réponds en texte naturel en français."
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


def build_system_prompt(profil_complet: dict[str, Any]) -> str:
    """Prompt système à partir du JSON GET /onboarding/{id}/complet."""
    ctx = PromptContext.from_complet(profil_complet)
    nombre = ctx.foyer.nombre_personnes if ctx.foyer else 1
    return "\n\n".join(
        [
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
            RULE_NO_HALLUCINATION,
            RULE_FOOD_SAFETY,
            OUTPUT_FORMAT,
        ]
    )


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
            }
            for r in candidats
        ],
        ensure_ascii=False,
    )
    return (
        f"Génère un planning de repas pour {nb_jours} jours à partir du {date_debut.isoformat()}, "
        "un repas par créneau (petit_dejeuner, dejeuner, diner) et par jour. "
        f"Choisis UNIQUEMENT parmi ces recettes (n'invente jamais de recette_id) : {recettes_json}\n\n"
        f"Réponds UNIQUEMENT avec un tableau JSON de la forme {PLANNING_JSON_SHAPE}, "
        "sans texte ni markdown autour."
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
    membres = ", ".join(
        f"{m.age_approx} ans" + ("" if m.regime_aligne else " (régime différent)")
        for m in foyer.membres
    )
    return f"{ligne} Membres : {membres}." if membres else ligne


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
    if preferences.aliments_detestes:
        lignes.append(
            "Aliments à éviter par préférence (non médical) : "
            f"{_join_or_aucun(preferences.aliments_detestes)}."
        )
    return "\n".join(lignes)


def _describe_budget(budget: BudgetOut | None) -> str:
    if budget is None:
        return "Budget disponible : non renseigné."
    return f"Budget disponible : {budget.montant_restant} Ar restants sur la {budget.periode}."


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
