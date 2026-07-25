from backend.services.recipe_rag import filtrer_recettes_compatibles


def test_aliments_aimes_priorises_dans_le_ranking():
    recettes = [
        {
            "id": "1",
            "nom": "salade",
            "tags": ["dejeuner"],
            "ingredients": [{"nom": "tomate", "poids_requis": 1, "unite": "g", "ingredient_id": "a"}],
        },
        {
            "id": "2",
            "nom": "poulet riz",
            "tags": ["dejeuner"],
            "ingredients": [
                {"nom": "poulet", "poids_requis": 1, "unite": "g", "ingredient_id": "b"},
                {"nom": "riz", "poids_requis": 1, "unite": "g", "ingredient_id": "c"},
            ],
        },
    ]
    prefs = {"allergies": [], "tabous": [], "aliments_detestes": [], "aliments_aimes": ["poulet", "riz"]}
    result = filtrer_recettes_compatibles(recettes, prefs, foyer={})
    assert result[0]["id"] == "2"


def test_allergie_exclut_malgre_aliments_aimes():
    recettes = [
        {
            "id": "1",
            "nom": "arachide",
            "tags": ["dejeuner", "leger"],
            "ingredients": [{"nom": "arachide", "poids_requis": 1, "unite": "g", "ingredient_id": "a"}],
        },
        {
            "id": "2",
            "nom": "riz",
            "tags": ["dejeuner"],
            "ingredients": [{"nom": "riz", "poids_requis": 1, "unite": "g", "ingredient_id": "b"}],
        },
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
