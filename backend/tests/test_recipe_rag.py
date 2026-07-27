from backend.services.recipe_rag import (
    filtrer_recettes_compatibles,
    rank_recettes,
    selectionner_recettes_semaine,
)


def _recette(rid, nom, tags, ingredients, duree=30):
    return {
        "id": rid,
        "nom": nom,
        "tags": tags,
        "duree_minutes": duree,
        "ingredients": [
            {"nom": n, "poids_requis": 1, "unite": "g", "ingredient_id": f"i-{n}"}
            for n in ingredients
        ],
    }


def test_aliments_aimes_priorises_dans_le_ranking():
    recettes = [
        _recette("1", "salade", ["dejeuner"], ["tomate"]),
        _recette("2", "poulet riz", ["dejeuner"], ["poulet", "riz"]),
    ]
    prefs = {
        "allergies": [],
        "tabous": [],
        "aliments_detestes": [],
        "aliments_aimes": ["poulet", "riz"],
    }
    result = filtrer_recettes_compatibles(recettes, prefs, foyer={})
    assert result[0]["id"] == "2"
    assert result[0]["_rank_score"] > result[1]["_rank_score"]


def test_allergie_exclut_malgre_aliments_aimes():
    recettes = [
        _recette("1", "arachide", ["dejeuner", "leger"], ["arachide"]),
        _recette("2", "riz", ["dejeuner"], ["riz"]),
    ]
    prefs = {
        "objectif": "perte_poids",
        "allergies": ["arachide"],
        "tabous": [],
        "aliments_detestes": [],
        "aliments_aimes": ["arachide"],
    }
    result = filtrer_recettes_compatibles(recettes, prefs, foyer={})
    assert [r["id"] for r in result] == ["2"]


def test_rank_recettes_objectif_et_jaccard():
    recettes = [
        _recette("a", "aaa_leger", ["dejeuner", "leger"], ["tomate"]),
        _recette("b", "bbb_riche", ["dejeuner", "riche"], ["poulet", "riz"]),
    ]
    prefs = {
        "objectif": "perte_poids",
        "aliments_aimes": ["poulet"],
        "allergies": [],
        "tabous": [],
        "aliments_detestes": [],
    }
    ranked = rank_recettes(recettes, prefs, foyer={})
    # tag leger (+2) bat jaccard partiel sur poulet
    assert ranked[0]["id"] == "a"
    assert "_rank_score" in ranked[0]


def test_rank_recettes_recent_ids_penalty():
    recettes = [
        _recette("1", "alpha", ["diner"], ["riz"]),
        _recette("2", "beta", ["diner"], ["riz"]),
    ]
    prefs = {"allergies": [], "tabous": [], "aliments_detestes": [], "aliments_aimes": []}
    ranked = rank_recettes(recettes, prefs, foyer={}, recent_ids={"1"})
    assert ranked[0]["id"] == "2"
    assert ranked[1]["_rank_score"] < ranked[0]["_rank_score"]


def test_rank_recettes_duree_max_bonus():
    recettes = [
        _recette("slow", "slow", ["diner"], ["riz"], duree=60),
        _recette("fast", "fast", ["diner"], ["riz"], duree=15),
    ]
    prefs = {"allergies": [], "tabous": [], "aliments_detestes": [], "aliments_aimes": []}
    ranked = rank_recettes(recettes, prefs, foyer={}, duree_max=20)
    assert ranked[0]["id"] == "fast"


def test_selectionner_recettes_semaine_uses_rank():
    recettes = [
        _recette("low", "zzz_low", ["petit_dejeuner", "dejeuner", "diner"], ["tomate"]),
        _recette("high", "aaa_high", ["petit_dejeuner", "dejeuner", "diner"], ["poulet"]),
    ]
    prefs = {
        "aliments_aimes": ["poulet"],
        "allergies": [],
        "tabous": [],
        "aliments_detestes": [],
    }
    ranked = rank_recettes(recettes, prefs, foyer={})
    selection = selectionner_recettes_semaine(ranked, nb_jours=1)
    assert len(selection) == 3
    assert all(s["id"] == "high" for s in selection)
