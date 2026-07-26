from typing import Optional

from pydantic import BaseModel, Field


class StockImportLine(BaseModel):
    label: str
    quantite: float
    unite: str
    ingredient_id: Optional[str] = None
    matched: bool = False


class StockImportTextRequest(BaseModel):
    text: str = Field(min_length=1)
    apply: bool = False


class StockImportTextResponse(BaseModel):
    lines: list[StockImportLine]
    applied: int = 0
