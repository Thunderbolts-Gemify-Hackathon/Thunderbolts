from pydantic import BaseModel, Field


class AntiGaspiOut(BaseModel):
    ariary_sauves: float = 0
    items_sauves: int = 0
    streak_jours: int = 0
    message: str = ""
