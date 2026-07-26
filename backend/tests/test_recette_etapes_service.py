import pytest

from backend.services import recette_etapes_service
from backend.tests.factories import make_planning_repas, make_stock_profil


class FakeGemmaClient:
    def __init__(self, content: str):
        self._content = content

    def chat(self, messages, tools=None, *, json_mode: bool = False):
        assert tools is None, "cet appel ne doit jamais passer d'outils (pas de tool loop)"
        assert json_mode is True, "les étapes doivent être demandées en JSON structuré"
        return {"message": {"role": "assistant", "content": self._content}}


def _setup_recette(db):
    profil, riz, poulet = make_stock_profil(db, with_budget=False)
    _, repas = make_planning_repas(db, profil, riz, poulet)
    return repas.recette_id


def test_generer_etapes_parse_le_json_structure(db_session):
    recette_id = _setup_recette(db_session)
    contenu = (
        '[{"titre": "Faire cuire le riz.", "ingredients": ["Riz"]}, '
        '{"titre": "Ajouter le poulet.", "ingredients": ["Poulet", "Ingredient inconnu"]}]'
    )
    client = FakeGemmaClient(contenu)
    etapes = recette_etapes_service.generer_etapes(db_session, recette_id, client=client)

    assert [e.numero for e in etapes] == [1, 2]
    assert etapes[0].titre == "Faire cuire le riz."
    # "Riz" (casse du modèle) est retrouvé et normalisé vers le nom réel en base ("riz")
    assert etapes[0].ingredients == ["riz"]
    # l'ingrédient inventé par le modèle est filtré, seul "poulet" (réel) reste
    assert etapes[1].ingredients == ["poulet"]


def test_generer_etapes_json_dans_une_fence_markdown(db_session):
    recette_id = _setup_recette(db_session)
    # Une seule étape JSON → fallback multi-étapes (mode cuisine a besoin de plusieurs)
    contenu = '```json\n[{"titre": "Servir chaud.", "ingredients": []}]\n```'
    client = FakeGemmaClient(contenu)
    etapes = recette_etapes_service.generer_etapes(db_session, recette_id, client=client)
    assert len(etapes) >= 3
    assert all("{" not in e.titre for e in etapes)


def test_generer_etapes_refuse_json_brut_comme_titre(db_session):
    recette_id = _setup_recette(db_session)
    client = FakeGemmaClient('{"titre": "Couper", "ingredients": []}')
    etapes = recette_etapes_service.generer_etapes(db_session, recette_id, client=client)
    assert len(etapes) >= 3
    assert all("{" not in e.titre and "[" not in e.titre for e in etapes)


def test_generer_etapes_repli_texte_si_pas_de_json(db_session):
    recette_id = _setup_recette(db_session)
    client = FakeGemmaClient("1. Faire cuire le riz.\n2. Ajouter le poulet.")
    etapes = recette_etapes_service.generer_etapes(db_session, recette_id, client=client)
    assert [e.titre for e in etapes] == ["Faire cuire le riz.", "Ajouter le poulet."]


def test_generer_etapes_recette_introuvable(db_session):
    with pytest.raises(ValueError):
        recette_etapes_service.generer_etapes(db_session, "id-inexistant", client=FakeGemmaClient("x"))


def test_generer_etapes_reponse_vide_utilise_fallback(db_session):
    recette_id = _setup_recette(db_session)
    client = FakeGemmaClient("")
    etapes = recette_etapes_service.generer_etapes(db_session, recette_id, client=client)
    assert len(etapes) >= 3
    assert etapes[0].numero == 1
    assert "ingrédients" in etapes[0].titre.lower() or "ingredient" in etapes[0].titre.lower()


def test_generer_etapes_accepte_enveloppe_etapes(db_session):
    """Gemma renvoie parfois {"etapes": [...]} — plusieurs items sont gardés."""
    recette_id = _setup_recette(db_session)
    contenu = (
        '{"etapes": ['
        '{"titre": "Couper le poulet.", "ingredients": ["poulet"]},'
        '{"titre": "Faire cuire le riz.", "ingredients": ["riz"]}'
        "]}"
    )
    client = FakeGemmaClient(contenu)
    etapes = recette_etapes_service.generer_etapes(db_session, recette_id, client=client)
    assert len(etapes) == 2
    assert etapes[0].titre == "Couper le poulet."
    assert etapes[0].ingredients == ["poulet"]
    assert etapes[1].ingredients == ["riz"]
