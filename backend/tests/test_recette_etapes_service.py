import pytest

from backend.services import recette_etapes_service
from backend.tests.factories import make_planning_repas, make_stock_profil


class FakeGemmaClient:
    def __init__(self, content: str):
        self._content = content

    def chat(self, messages, tools=None):
        assert tools is None, "cet appel ne doit jamais passer d'outils (pas de tool loop)"
        return {"message": {"role": "assistant", "content": self._content}}


def _setup_recette(db):
    profil, riz, poulet = make_stock_profil(db, with_budget=False)
    _, repas = make_planning_repas(db, profil, riz, poulet)
    return repas.recette_id


def test_generer_etapes_retourne_le_contenu_gemma(db_session):
    recette_id = _setup_recette(db_session)
    client = FakeGemmaClient("1. **Faire cuire le riz.**\nriz")
    etapes = recette_etapes_service.generer_etapes(db_session, recette_id, client=client)
    assert "riz" in etapes


def test_generer_etapes_recette_introuvable(db_session):
    with pytest.raises(ValueError):
        recette_etapes_service.generer_etapes(db_session, "id-inexistant", client=FakeGemmaClient("x"))


def test_generer_etapes_reponse_vide_leve_runtime_error(db_session):
    recette_id = _setup_recette(db_session)
    client = FakeGemmaClient("")
    with pytest.raises(RuntimeError):
        recette_etapes_service.generer_etapes(db_session, recette_id, client=client)
