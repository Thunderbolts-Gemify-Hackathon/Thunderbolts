from fastapi import APIRouter

router = APIRouter(prefix="/social", tags=["social"])

_DEFIS = [
    {
        "id": "budget-semaine",
        "titre": "Semaine sous 50 000 Ar",
        "description": "Tiens ton budget courses sous 50 000 Ar cette semaine.",
        "type": "budget",
        "objectif": 50000,
        "unite": "Ar",
    },
    {
        "id": "anti-gaspi-3j",
        "titre": "Zéro gaspi 3 jours",
        "description": "Utilise tout ce qui périme dans les 3 jours.",
        "type": "anti_gaspi",
        "objectif": 3,
        "unite": "jours",
    },
    {
        "id": "fait-maison",
        "titre": "5 repas maison",
        "description": "Valide 5 repas cuisinés à la maison.",
        "type": "repas",
        "objectif": 5,
        "unite": "repas",
    },
]


@router.get("/defis")
def list_defis():
    return _DEFIS
