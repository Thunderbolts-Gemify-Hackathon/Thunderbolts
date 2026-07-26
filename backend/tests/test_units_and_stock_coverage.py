from backend.services.stock_coverage import avec_couverture
from backend.services.units import convert_quantity, quantite_suffisante, to_base


def test_to_base_kg_et_litre():
    assert to_base(1, "kg") == (1000.0, "g")
    assert to_base(2, "l") == (2000.0, "ml")
    assert to_base(150, "g") == (150.0, "g")


def test_convert_quantity_kg_vers_g():
    assert convert_quantity(1, "kg", "g") == 1000.0
    assert convert_quantity(500, "g", "kg") == 0.5
    assert convert_quantity(1, "kg", "ml") is None


def test_quantite_suffisante_avec_unites_differentes():
    # 1 kg en stock couvre 200 g de recette
    assert quantite_suffisante(1, "kg", 200, "g") is True
    assert quantite_suffisante(100, "g", 200, "g") is False
    assert quantite_suffisante(1, "l", 200, "g") is False


def test_avec_couverture_respecte_les_unites():
    recette = {
        "id": "r1",
        "nom": "riz",
        "ingredients": [
            {"ingredient_id": "riz", "nom": "riz", "poids_requis": 200, "unite": "g"},
            {"ingredient_id": "eau", "nom": "eau", "poids_requis": 300, "unite": "ml"},
        ],
    }
    stock = {
        "riz": (1.0, "kg"),  # largement assez
        # eau manquante
    }
    scored = avec_couverture(recette, stock)
    assert scored["_couverture"] == 0.5
    assert scored["_manquants"] == ["eau"]

    stock["eau"] = (1.0, "l")
    scored = avec_couverture(recette, stock)
    assert scored["_couverture"] == 1.0
    assert scored["_manquants"] == []
