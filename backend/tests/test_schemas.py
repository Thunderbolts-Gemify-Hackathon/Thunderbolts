from pydantic import ValidationError
import pytest

from backend.schemas.composites import StockDeductionRequest
from backend.schemas.ingredient import IngredientOut


def test_stock_deduction_quantite_positive():
    assert StockDeductionRequest(ingredient_id="i1", quantite=10).quantite == 10
    with pytest.raises(ValidationError):
        StockDeductionRequest(ingredient_id="i1", quantite=0)


def test_ingredient_out_from_attributes():
    class Obj:
        id = "1"
        nom = "riz"
        unite_defaut = "g"

    assert IngredientOut.model_validate(Obj()).nom == "riz"
