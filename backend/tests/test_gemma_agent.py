from backend.services.gemma_agent import parse_json_list, run_tool_loop


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


class _LoopingClient:
    """Simule un modèle qui rappelle toujours le même outil."""

    def __init__(self):
        self.calls = 0

    def chat(self, messages, tools=None, *, json_mode=False):
        self.calls += 1
        if tools:
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "name": "find_nearest_supermarkets",
                            "arguments": {},
                        }
                    ],
                }
            }
        return {
            "message": {
                "role": "assistant",
                "content": "Le marché le plus proche est Analakely, à environ 1 km.",
            }
        }


def test_run_tool_loop_coupe_les_rappels_identiques(db_session, monkeypatch):
    from backend.services import gemma_agent

    monkeypatch.setattr(
        gemma_agent,
        "execute_tool_call",
        lambda *_a, **_k: {"ok": True, "points": [{"nom": "Analakely"}]},
    )
    client = _LoopingClient()
    answer = run_tool_loop(
        db_session,
        client,
        [{"role": "user", "content": "où est le marché"}],
        profil_id="profil-test",
        max_iterations=5,
    )
    assert "Analakely" in answer
    # tour 1 outil → exécution → tour 2 (même signature) → force answer (tour 3)
    assert client.calls == 3


def test_run_tool_loop_sans_outils_un_seul_tour():
    class _Once:
        def chat(self, messages, tools=None, *, json_mode=False):
            assert tools is None
            return {"message": {"role": "assistant", "content": "ok planning"}}

    assert (
        run_tool_loop(
            None,  # type: ignore[arg-type]
            _Once(),
            [{"role": "user", "content": "x"}],
            profil_id="p",
            tools=[],
        )
        == "ok planning"
    )