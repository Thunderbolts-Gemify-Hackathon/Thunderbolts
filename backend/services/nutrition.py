from fastapi import HTTPException

FACTEUR_ACTIVITE = {
    "sedentaire": 1.2,
    "leger": 1.375,
    "modere": 1.55,
    "actif": 1.725,
    "tres_actif": 1.9,
}


def calculer_imc(poids: float, taille_cm: float) -> float:
    taille_m = taille_cm / 100.0
    if taille_m <= 0:
        raise HTTPException(status_code=400, detail="Taille invalide pour le calcul d'IMC")
    return round(poids / (taille_m**2), 2)


def calculer_besoin_calorique(
    age: int,
    sexe: str,
    poids: float,
    taille_cm: float,
    niveau_activite: str,
) -> float:
    if sexe.lower() in {"homme", "male", "m", "h"}:
        bmr = 10 * poids + 6.25 * taille_cm - 5 * age + 5
    else:
        bmr = 10 * poids + 6.25 * taille_cm - 5 * age - 161

    facteur = FACTEUR_ACTIVITE.get(niveau_activite)
    if facteur is None:
        raise HTTPException(status_code=400, detail=f"Niveau d'activité inconnu: {niveau_activite}")
    return round(bmr * facteur, 1)
