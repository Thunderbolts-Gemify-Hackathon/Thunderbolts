from datetime import time

INGREDIENTS = {
    "riz": "g",
    "bredes mafana": "g",
    "poulet": "g",
    "pois du cap": "g",
    "tomate": "g",
    "oignon": "g",
    "huile": "ml",
    "sel": "g",
    "ail": "g",
    "gingembre": "g",
    "poisson": "g",
    "haricot": "g",
    "canard": "g",
    "pois chiches": "g",
    "arachide": "g",
}

RECETTES = {
    "ravitoto sy henakisoa": (
        time(12, 0), 720, 28, 55, 38, ["dejeuner"],
        [("bredes mafana", 300, "g"), ("arachide", 80, "g"), ("riz", 200, "g"), ("oignon", 50, "g"), ("huile", 20, "ml"), ("sel", 3, "g")],
    ),
    "romazava": (
        time(12, 30), 580, 32, 40, 22, ["dejeuner"],
        [("poulet", 200, "g"), ("bredes mafana", 150, "g"), ("tomate", 100, "g"), ("oignon", 60, "g"), ("gingembre", 10, "g"), ("riz", 180, "g")],
    ),
    "poisson coco riz": (
        time(19, 0), 650, 30, 60, 24, ["diner"],
        [("poisson", 220, "g"), ("riz", 200, "g"), ("tomate", 80, "g"), ("oignon", 40, "g"), ("ail", 8, "g"), ("huile", 15, "ml")],
    ),
    "poulet coco": (
        time(12, 0), 690, 35, 45, 32, ["dejeuner"],
        [("poulet", 250, "g"), ("oignon", 50, "g"), ("ail", 10, "g"), ("gingembre", 8, "g"), ("riz", 200, "g"), ("huile", 20, "ml")],
    ),
    "achard": (
        time(12, 0), 180, 4, 20, 8, ["accompagnement"],
        [("oignon", 100, "g"), ("tomate", 80, "g"), ("huile", 25, "ml"), ("sel", 4, "g"), ("gingembre", 5, "g")],
    ),
    "varenga": (
        time(19, 0), 620, 40, 35, 28, ["diner"],
        [("poulet", 280, "g"), ("oignon", 70, "g"), ("ail", 10, "g"), ("riz", 200, "g"), ("huile", 15, "ml"), ("sel", 3, "g")],
    ),
    "hen'omby ritra": (
        time(12, 0), 700, 38, 42, 30, ["dejeuner"],
        [("canard", 250, "g"), ("oignon", 60, "g"), ("ail", 10, "g"), ("gingembre", 10, "g"), ("riz", 200, "g"), ("huile", 15, "ml")],
    ),
    "voanjobory sy henakisoa": (
        time(12, 30), 640, 26, 70, 18, ["dejeuner"],
        [("pois du cap", 200, "g"), ("oignon", 50, "g"), ("tomate", 80, "g"), ("ail", 8, "g"), ("riz", 180, "g"), ("huile", 15, "ml")],
    ),
    "lasopy": (
        time(19, 0), 320, 12, 35, 10, ["diner"],
        [("haricot", 150, "g"), ("tomate", 80, "g"), ("oignon", 50, "g"), ("ail", 6, "g"), ("gingembre", 5, "g"), ("huile", 10, "ml")],
    ),
    "kitoza oeufs riz": (
        time(7, 30), 480, 22, 50, 16, ["petit_dejeuner"],
        [("poulet", 100, "g"), ("oignon", 30, "g"), ("riz", 150, "g"), ("huile", 10, "ml"), ("sel", 2, "g")],
    ),
    "salade pois chiches": (
        time(12, 0), 350, 14, 40, 12, ["dejeuner"],
        [("pois chiches", 180, "g"), ("tomate", 100, "g"), ("oignon", 40, "g"), ("huile", 20, "ml"), ("sel", 3, "g")],
    ),
    "canard aux bredes": (
        time(19, 0), 710, 36, 38, 35, ["diner"],
        [("canard", 250, "g"), ("bredes mafana", 200, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("riz", 200, "g"), ("huile", 15, "ml")],
    ),
}
