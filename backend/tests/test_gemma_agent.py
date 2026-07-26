from backend.services.gemma_agent import parse_json_list


def test_parse_json_list_tableau_valide():
    assert parse_json_list('[{"a": 1}, {"a": 2}]') == [{"a": 1}, {"a": 2}]


def test_parse_json_list_fence_markdown():
    contenu = '```json\n[{"a": 1}]\n```'
    assert parse_json_list(contenu) == [{"a": 1}]


def test_parse_json_list_objet_unique_normalise_en_liste():
    """Sur un planning à 1 jour, les petits modèles renvoient parfois un objet nu
    au lieu d'un tableau à un élément : on doit l'accepter quand même."""
    contenu = '{"jour": "2026-07-27", "type_repas": "dejeuner", "recette_id": "abc"}'
    assert parse_json_list(contenu) == [
        {"jour": "2026-07-27", "type_repas": "dejeuner", "recette_id": "abc"}
    ]


def test_parse_json_list_objet_unique_dans_texte_libre():
    contenu = "Voici le repas :\n{\"recette_id\": \"abc\"}\nVoilà."
    assert parse_json_list(contenu) == [{"recette_id": "abc"}]


def test_parse_json_list_invalide_retourne_none():
    assert parse_json_list("pas du json du tout") is None
    assert parse_json_list("") is None
    assert parse_json_list("42") is None
