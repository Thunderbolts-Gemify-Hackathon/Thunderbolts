from datetime import time

# Catalogue produits : unite + métadonnées catalogue (pas de vectorisation).
# prix_moyen_reference = Ar / kg (g), / L (ml), ou / unité.
INGREDIENTS = {
    "riz": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 365,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2500.0,
    },
    "bredes mafana": {
        "unite": "g",
        "categorie": "légume",
        "conservation_jours": 3,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 1500.0,
    },
    "poulet": {
        "unite": "g",
        "categorie": "protéine",
        "conservation_jours": 2,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 12000.0,
    },
    "pois du cap": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 365,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 4000.0,
    },
    "tomate": {
        "unite": "g",
        "categorie": "légume",
        "conservation_jours": 5,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2000.0,
    },
    "oignon": {
        "unite": "g",
        "categorie": "légume",
        "conservation_jours": 30,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 1800.0,
    },
    "huile": {
        "unite": "ml",
        "categorie": "condiment",
        "conservation_jours": 180,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 5000.0,
    },
    "sel": {
        "unite": "g",
        "categorie": "condiment",
        "conservation_jours": 730,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 500.0,
    },
    "ail": {
        "unite": "g",
        "categorie": "épice",
        "conservation_jours": 60,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 3000.0,
    },
    "gingembre": {
        "unite": "g",
        "categorie": "épice",
        "conservation_jours": 14,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2500.0,
    },
    "poisson": {
        "unite": "g",
        "categorie": "protéine",
        "conservation_jours": 1,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 10000.0,
    },
    "haricot": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 365,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 3500.0,
    },
    "canard": {
        "unite": "g",
        "categorie": "protéine",
        "conservation_jours": 2,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 15000.0,
    },
    "pois chiches": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 365,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 4500.0,
    },
    "arachide": {
        "unite": "g",
        "categorie": "protéine",
        "conservation_jours": 180,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 6000.0,
    },
    "oeuf": {
        "unite": "unite",
        "categorie": "protéine",
        "conservation_jours": 14,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 800.0,
    },
    "lait de coco": {
        "unite": "ml",
        "categorie": "condiment",
        "conservation_jours": 3,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 6000.0,
    },
    "carotte": {
        "unite": "g",
        "categorie": "légume",
        "conservation_jours": 10,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2200.0,
    },
    "chou": {
        "unite": "g",
        "categorie": "légume",
        "conservation_jours": 7,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 1800.0,
    },
    "banane": {
        "unite": "g",
        "categorie": "fruit",
        "conservation_jours": 5,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2500.0,
    },
    "patate douce": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 14,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2000.0,
    },
    "manioc": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 5,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 1500.0,
    },
    "lentilles": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 365,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 5000.0,
    },
    "nouilles": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 365,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 4000.0,
    },
    "miel": {
        "unite": "g",
        "categorie": "condiment",
        "conservation_jours": 730,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 12000.0,
    },
    "citron": {
        "unite": "unite",
        "categorie": "fruit",
        "conservation_jours": 14,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 500.0,
    },
    "mais": {
        "unite": "g",
        "categorie": "féculent",
        "conservation_jours": 3,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2000.0,
    },
    "cresson": {
        "unite": "g",
        "categorie": "légume",
        "conservation_jours": 3,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 1600.0,
    },
    "aubergine": {
        "unite": "g",
        "categorie": "légume",
        "conservation_jours": 5,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2500.0,
    },
    "courgette": {
        "unite": "g",
        "categorie": "légume",
        "conservation_jours": 5,
        "saison": ["toute_saison"],
        "prix_moyen_reference": 2300.0,
    },
}

# (heure, kcal, prot, gluc, lip, duree, tags, ingredients)
RECETTES = {
    "ravitoto sy henakisoa": (
        time(12, 0), 720, 28, 55, 38, 35, ["dejeuner"],
        [("bredes mafana", 300, "g"), ("arachide", 80, "g"), ("riz", 200, "g"), ("oignon", 50, "g"), ("huile", 20, "ml"), ("sel", 3, "g")],
    ),
    "romazava": (
        time(12, 30), 580, 32, 40, 22, 30, ["dejeuner"],
        [("poulet", 200, "g"), ("bredes mafana", 150, "g"), ("tomate", 100, "g"), ("oignon", 60, "g"), ("gingembre", 10, "g"), ("riz", 180, "g")],
    ),
    "poisson coco riz": (
        time(19, 0), 650, 30, 60, 24, 25, ["diner"],
        [("poisson", 220, "g"), ("riz", 200, "g"), ("tomate", 80, "g"), ("oignon", 40, "g"), ("ail", 8, "g"), ("huile", 15, "ml")],
    ),
    "poulet coco": (
        time(12, 0), 690, 35, 45, 32, 35, ["dejeuner"],
        [("poulet", 250, "g"), ("oignon", 50, "g"), ("ail", 10, "g"), ("gingembre", 8, "g"), ("riz", 200, "g"), ("huile", 20, "ml")],
    ),
    "achard": (
        time(12, 0), 180, 4, 20, 8, 10, ["accompagnement"],
        [("oignon", 100, "g"), ("tomate", 80, "g"), ("huile", 25, "ml"), ("sel", 4, "g"), ("gingembre", 5, "g")],
    ),
    "varenga": (
        time(19, 0), 620, 40, 35, 28, 25, ["diner"],
        [("poulet", 280, "g"), ("oignon", 70, "g"), ("ail", 10, "g"), ("riz", 200, "g"), ("huile", 15, "ml"), ("sel", 3, "g")],
    ),
    "hen'omby ritra": (
        time(12, 0), 700, 38, 42, 30, 45, ["dejeuner"],
        [("canard", 250, "g"), ("oignon", 60, "g"), ("ail", 10, "g"), ("gingembre", 10, "g"), ("riz", 200, "g"), ("huile", 15, "ml")],
    ),
    "voanjobory sy henakisoa": (
        time(12, 30), 640, 26, 70, 18, 40, ["dejeuner"],
        [("pois du cap", 200, "g"), ("oignon", 50, "g"), ("tomate", 80, "g"), ("ail", 8, "g"), ("riz", 180, "g"), ("huile", 15, "ml")],
    ),
    "lasopy": (
        time(19, 0), 320, 12, 35, 10, 30, ["diner"],
        [("haricot", 150, "g"), ("tomate", 80, "g"), ("oignon", 50, "g"), ("ail", 6, "g"), ("gingembre", 5, "g"), ("huile", 10, "ml")],
    ),
    "kitoza oeufs riz": (
        time(7, 30), 480, 22, 50, 16, 15, ["petit_dejeuner"],
        [("poulet", 100, "g"), ("oignon", 30, "g"), ("riz", 150, "g"), ("huile", 10, "ml"), ("sel", 2, "g")],
    ),
    "salade pois chiches": (
        time(12, 0), 350, 14, 40, 12, 15, ["dejeuner"],
        [("pois chiches", 180, "g"), ("tomate", 100, "g"), ("oignon", 40, "g"), ("huile", 20, "ml"), ("sel", 3, "g")],
    ),
    "canard aux bredes": (
        time(19, 0), 710, 36, 38, 35, 40, ["diner"],
        [("canard", 250, "g"), ("bredes mafana", 200, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("riz", 200, "g"), ("huile", 15, "ml")],
    ),
    # --- Nouvelles recettes étudiantes / malagasy ---
    "vary amin'anana": (
        time(12, 0), 420, 12, 65, 10, 25, ["dejeuner", "rapide"],
        [("riz", 200, "g"), ("bredes mafana", 200, "g"), ("oignon", 40, "g"), ("huile", 15, "ml"), ("sel", 3, "g")],
    ),
    "tsaramaso sy henakisoa": (
        time(12, 30), 610, 28, 55, 22, 40, ["dejeuner"],
        [("haricot", 200, "g"), ("poulet", 150, "g"), ("oignon", 50, "g"), ("tomate", 80, "g"), ("riz", 180, "g"), ("huile", 15, "ml")],
    ),
    "akoho gasy": (
        time(19, 0), 680, 36, 40, 30, 45, ["diner"],
        [("poulet", 280, "g"), ("ail", 12, "g"), ("gingembre", 10, "g"), ("oignon", 60, "g"), ("riz", 200, "g"), ("huile", 20, "ml")],
    ),
    "soupe tomate ail": (
        time(19, 0), 220, 6, 28, 8, 20, ["diner", "rapide", "leger"],
        [("tomate", 300, "g"), ("ail", 10, "g"), ("oignon", 40, "g"), ("huile", 10, "ml"), ("sel", 3, "g")],
    ),
    "riz saute legumes": (
        time(12, 0), 480, 12, 70, 14, 20, ["dejeuner", "rapide"],
        [("riz", 220, "g"), ("carotte", 80, "g"), ("oignon", 50, "g"), ("oeuf", 1, "unite"), ("huile", 20, "ml"), ("sel", 3, "g")],
    ),
    "haricots coco": (
        time(12, 30), 560, 18, 60, 22, 35, ["dejeuner"],
        [("haricot", 200, "g"), ("lait de coco", 150, "ml"), ("oignon", 40, "g"), ("ail", 8, "g"), ("riz", 180, "g")],
    ),
    "poisson grille riz": (
        time(19, 0), 580, 32, 55, 16, 25, ["diner", "rapide"],
        [("poisson", 220, "g"), ("riz", 200, "g"), ("citron", 1, "unite"), ("ail", 6, "g"), ("huile", 10, "ml"), ("sel", 3, "g")],
    ),
    "omelette tomate": (
        time(7, 30), 320, 18, 8, 22, 10, ["petit_dejeuner", "rapide"],
        [("oeuf", 2, "unite"), ("tomate", 80, "g"), ("oignon", 30, "g"), ("huile", 10, "ml"), ("sel", 2, "g")],
    ),
    "bouillon gingembre": (
        time(7, 0), 80, 1, 12, 1, 10, ["petit_dejeuner", "rapide", "leger"],
        [("gingembre", 20, "g"), ("citron", 1, "unite"), ("miel", 10, "g")],
    ),
    "salade tomate oignon": (
        time(12, 0), 160, 3, 14, 10, 8, ["dejeuner", "accompagnement", "rapide"],
        [("tomate", 200, "g"), ("oignon", 80, "g"), ("huile", 15, "ml"), ("sel", 3, "g"), ("citron", 1, "unite")],
    ),
    "poulet braise rapide": (
        time(19, 0), 620, 34, 35, 28, 30, ["diner"],
        [("poulet", 250, "g"), ("oignon", 50, "g"), ("ail", 10, "g"), ("tomate", 80, "g"), ("riz", 180, "g"), ("huile", 15, "ml")],
    ),
    "ravitoto leger": (
        time(12, 0), 520, 18, 48, 24, 30, ["dejeuner", "leger"],
        [("bredes mafana", 250, "g"), ("arachide", 50, "g"), ("riz", 180, "g"), ("oignon", 40, "g"), ("huile", 10, "ml")],
    ),
    "lasopy legume": (
        time(19, 0), 280, 8, 36, 8, 25, ["diner", "leger"],
        [("carotte", 120, "g"), ("chou", 100, "g"), ("tomate", 80, "g"), ("oignon", 40, "g"), ("huile", 10, "ml")],
    ),
    "voanjobory vegetarien": (
        time(12, 30), 540, 18, 72, 12, 35, ["dejeuner", "vegetarien"],
        [("pois du cap", 220, "g"), ("tomate", 100, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("riz", 180, "g")],
    ),
    "patate douce roti": (
        time(19, 0), 380, 6, 70, 8, 35, ["diner", "vegetarien"],
        [("patate douce", 300, "g"), ("huile", 15, "ml"), ("sel", 3, "g"), ("ail", 6, "g")],
    ),
    "manioc vapeur arachide": (
        time(12, 0), 450, 10, 75, 12, 40, ["dejeuner"],
        [("manioc", 300, "g"), ("arachide", 40, "g"), ("sel", 2, "g")],
    ),
    "nouilles oeuf etudiant": (
        time(19, 0), 520, 16, 65, 18, 15, ["diner", "rapide"],
        [("nouilles", 120, "g"), ("oeuf", 1, "unite"), ("oignon", 40, "g"), ("huile", 15, "ml"), ("ail", 5, "g")],
    ),
    "misao legumes": (
        time(12, 0), 480, 12, 62, 16, 20, ["dejeuner", "rapide"],
        [("nouilles", 130, "g"), ("carotte", 60, "g"), ("chou", 80, "g"), ("oignon", 40, "g"), ("huile", 20, "ml"), ("ail", 6, "g")],
    ),
    "brochettes poulet": (
        time(19, 0), 540, 32, 30, 24, 30, ["diner"],
        [("poulet", 250, "g"), ("oignon", 60, "g"), ("ail", 8, "g"), ("huile", 15, "ml"), ("riz", 180, "g")],
    ),
    "cresson ail": (
        time(12, 0), 200, 6, 12, 14, 15, ["accompagnement", "rapide"],
        [("cresson", 200, "g"), ("ail", 10, "g"), ("huile", 15, "ml"), ("sel", 2, "g")],
    ),
    "aubergine tomate": (
        time(19, 0), 320, 6, 30, 18, 30, ["diner", "vegetarien"],
        [("aubergine", 250, "g"), ("tomate", 150, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("huile", 20, "ml"), ("riz", 150, "g")],
    ),
    "courgette sautee": (
        time(12, 0), 240, 5, 18, 16, 15, ["accompagnement", "rapide"],
        [("courgette", 250, "g"), ("ail", 8, "g"), ("huile", 15, "ml"), ("sel", 2, "g")],
    ),
    "carotte gingembre": (
        time(12, 0), 180, 3, 22, 8, 15, ["accompagnement", "rapide"],
        [("carotte", 200, "g"), ("gingembre", 8, "g"), ("huile", 10, "ml"), ("sel", 2, "g")],
    ),
    "lentilles tomate": (
        time(12, 30), 480, 22, 60, 10, 35, ["dejeuner", "vegetarien"],
        [("lentilles", 180, "g"), ("tomate", 120, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("riz", 150, "g")],
    ),
    "pois du cap coco": (
        time(19, 0), 600, 18, 65, 24, 40, ["diner"],
        [("pois du cap", 200, "g"), ("lait de coco", 120, "ml"), ("oignon", 40, "g"), ("ail", 8, "g"), ("riz", 180, "g")],
    ),
    "poulet gingembre rapide": (
        time(12, 0), 560, 34, 32, 26, 25, ["dejeuner", "rapide"],
        [("poulet", 220, "g"), ("gingembre", 12, "g"), ("ail", 8, "g"), ("oignon", 40, "g"), ("riz", 180, "g"), ("huile", 15, "ml")],
    ),
    "poisson aigre doux": (
        time(19, 0), 540, 28, 48, 18, 30, ["diner"],
        [("poisson", 220, "g"), ("tomate", 100, "g"), ("oignon", 50, "g"), ("citron", 1, "unite"), ("riz", 180, "g"), ("huile", 12, "ml")],
    ),
    "soupe haricot": (
        time(19, 0), 300, 14, 40, 6, 30, ["diner", "leger"],
        [("haricot", 160, "g"), ("carotte", 60, "g"), ("oignon", 40, "g"), ("ail", 6, "g"), ("huile", 8, "ml")],
    ),
    "riz jaune etudiant": (
        time(12, 0), 440, 10, 72, 10, 25, ["dejeuner", "rapide"],
        [("riz", 220, "g"), ("tomate", 60, "g"), ("oignon", 40, "g"), ("huile", 15, "ml"), ("sel", 3, "g")],
    ),
    "achard carotte": (
        time(12, 0), 160, 2, 16, 10, 12, ["accompagnement", "rapide"],
        [("carotte", 150, "g"), ("oignon", 50, "g"), ("huile", 20, "ml"), ("sel", 3, "g"), ("gingembre", 5, "g")],
    ),
    "varenga leger": (
        time(19, 0), 480, 30, 28, 20, 25, ["diner", "leger"],
        [("poulet", 200, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("riz", 150, "g"), ("huile", 10, "ml")],
    ),
    "henakisoa sauce tomate": (
        time(12, 0), 640, 30, 45, 28, 35, ["dejeuner"],
        [("poulet", 220, "g"), ("tomate", 150, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("riz", 200, "g"), ("huile", 15, "ml")],
    ),
    "canard oignon": (
        time(19, 0), 700, 34, 35, 38, 45, ["diner"],
        [("canard", 250, "g"), ("oignon", 100, "g"), ("ail", 10, "g"), ("riz", 200, "g"), ("huile", 10, "ml")],
    ),
    "salade arachide": (
        time(12, 0), 340, 12, 20, 24, 10, ["dejeuner", "rapide"],
        [("arachide", 80, "g"), ("tomate", 100, "g"), ("oignon", 40, "g"), ("citron", 1, "unite"), ("sel", 2, "g")],
    ),
    "banane frit riz": (
        time(7, 30), 520, 8, 85, 14, 20, ["petit_dejeuner"],
        [("banane", 200, "g"), ("riz", 150, "g"), ("huile", 20, "ml"), ("sel", 1, "g")],
    ),
    "porridge riz miel": (
        time(7, 0), 360, 6, 70, 6, 20, ["petit_dejeuner"],
        [("riz", 120, "g"), ("miel", 15, "g"), ("banane", 100, "g")],
    ),
    "mais vapeur": (
        time(12, 0), 280, 8, 55, 4, 25, ["dejeuner", "rapide"],
        [("mais", 250, "g"), ("sel", 2, "g"), ("huile", 5, "ml")],
    ),
    "curry pois chiches": (
        time(19, 0), 520, 16, 58, 20, 30, ["diner", "vegetarien"],
        [("pois chiches", 200, "g"), ("tomate", 120, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("lait de coco", 100, "ml"), ("riz", 150, "g")],
    ),
    "dal lentilles": (
        time(12, 0), 460, 20, 62, 8, 30, ["dejeuner", "vegetarien"],
        [("lentilles", 180, "g"), ("oignon", 50, "g"), ("ail", 8, "g"), ("gingembre", 8, "g"), ("tomate", 80, "g"), ("riz", 150, "g")],
    ),
    "wok bredes": (
        time(19, 0), 300, 8, 22, 18, 15, ["diner", "rapide", "leger"],
        [("bredes mafana", 250, "g"), ("ail", 10, "g"), ("oignon", 40, "g"), ("huile", 20, "ml"), ("sel", 2, "g")],
    ),
    "bol pois chiches": (
        time(12, 0), 420, 16, 48, 14, 20, ["dejeuner", "vegetarien", "rapide"],
        [("pois chiches", 180, "g"), ("tomate", 80, "g"), ("carotte", 60, "g"), ("huile", 15, "ml"), ("citron", 1, "unite")],
    ),
    "bowl riz legumes": (
        time(12, 30), 480, 12, 70, 12, 25, ["dejeuner", "vegetarien"],
        [("riz", 200, "g"), ("carotte", 60, "g"), ("courgette", 80, "g"), ("oignon", 40, "g"), ("huile", 15, "ml")],
    ),
    "oeufs riz sauce": (
        time(7, 30), 420, 16, 50, 14, 15, ["petit_dejeuner", "rapide"],
        [("oeuf", 2, "unite"), ("riz", 160, "g"), ("tomate", 60, "g"), ("oignon", 30, "g"), ("huile", 10, "ml")],
    ),
    "soupe cresson": (
        time(19, 0), 180, 5, 16, 10, 20, ["diner", "leger"],
        [("cresson", 200, "g"), ("oignon", 40, "g"), ("ail", 6, "g"), ("huile", 10, "ml"), ("sel", 2, "g")],
    ),
    "poulet citron": (
        time(19, 0), 560, 34, 30, 24, 30, ["diner"],
        [("poulet", 240, "g"), ("citron", 1, "unite"), ("ail", 10, "g"), ("oignon", 40, "g"), ("riz", 180, "g"), ("huile", 12, "ml")],
    ),
    "haricot carotte": (
        time(12, 0), 440, 16, 62, 8, 35, ["dejeuner", "vegetarien"],
        [("haricot", 180, "g"), ("carotte", 100, "g"), ("oignon", 40, "g"), ("ail", 6, "g"), ("riz", 160, "g")],
    ),
    "poisson tomate rapide": (
        time(19, 0), 500, 28, 40, 16, 20, ["diner", "rapide"],
        [("poisson", 200, "g"), ("tomate", 120, "g"), ("oignon", 40, "g"), ("ail", 6, "g"), ("riz", 160, "g"), ("huile", 10, "ml")],
    ),
    "chou saute ail": (
        time(12, 0), 200, 4, 16, 12, 12, ["accompagnement", "rapide"],
        [("chou", 250, "g"), ("ail", 10, "g"), ("huile", 15, "ml"), ("sel", 2, "g")],
    ),
    "riz coco sucré": (
        time(7, 0), 400, 5, 65, 14, 25, ["petit_dejeuner"],
        [("riz", 150, "g"), ("lait de coco", 120, "ml"), ("miel", 10, "g"), ("banane", 80, "g")],
    ),
    "lentilles coco": (
        time(19, 0), 520, 18, 55, 18, 35, ["diner", "vegetarien"],
        [("lentilles", 180, "g"), ("lait de coco", 100, "ml"), ("oignon", 40, "g"), ("ail", 8, "g"), ("riz", 150, "g")],
    ),
    "aubergine riz": (
        time(12, 0), 460, 8, 65, 16, 30, ["dejeuner", "vegetarien"],
        [("aubergine", 220, "g"), ("riz", 200, "g"), ("tomate", 80, "g"), ("oignon", 40, "g"), ("huile", 15, "ml")],
    ),
    "patate douce oeuf": (
        time(7, 30), 420, 14, 55, 14, 25, ["petit_dejeuner"],
        [("patate douce", 220, "g"), ("oeuf", 1, "unite"), ("huile", 10, "ml"), ("sel", 2, "g")],
    ),
    "nouilles poulet": (
        time(19, 0), 580, 26, 60, 20, 25, ["diner", "rapide"],
        [("nouilles", 120, "g"), ("poulet", 150, "g"), ("oignon", 40, "g"), ("carotte", 50, "g"), ("huile", 15, "ml"), ("ail", 6, "g")],
    ),
    "salade carotte citron": (
        time(12, 0), 140, 2, 18, 6, 8, ["accompagnement", "rapide", "leger"],
        [("carotte", 180, "g"), ("citron", 1, "unite"), ("huile", 10, "ml"), ("sel", 2, "g")],
    ),
    "romazava leger": (
        time(19, 0), 420, 24, 30, 14, 25, ["diner", "leger"],
        [("poulet", 150, "g"), ("bredes mafana", 180, "g"), ("tomate", 80, "g"), ("oignon", 40, "g"), ("gingembre", 8, "g")],
    ),
    "pois chiches riz": (
        time(12, 0), 500, 16, 72, 10, 25, ["dejeuner", "vegetarien"],
        [("pois chiches", 180, "g"), ("riz", 200, "g"), ("oignon", 40, "g"), ("tomate", 60, "g"), ("huile", 12, "ml")],
    ),
}

RECETTE_INSTRUCTIONS = {
    "ravitoto sy henakisoa": (
        "Faire revenir l'oignon, ajouter les brèdes et l'arachide. "
        "Mijoter, servir avec le riz."
    ),
    "romazava": (
        "Faire revenir oignon et gingembre, ajouter le poulet puis les brèdes et tomates. "
        "Mijoter et servir avec le riz."
    ),
    "poisson coco riz": (
        "Faire revenir ail et oignon, ajouter le poisson et la tomate. "
        "Assaisonner, servir avec le riz."
    ),
    "poulet coco": (
        "Faire revenir oignon, ail et gingembre, saisir le poulet. "
        "Mijoter puis servir avec le riz."
    ),
    "achard": "Couper finement oignon et tomate, assaisonner à l'huile, gingembre et sel.",
    "varenga": (
        "Effilocher le poulet cuit, le faire revenir avec oignon et ail. "
        "Servir avec le riz."
    ),
    "hen'omby ritra": (
        "Faire revenir oignon, ail et gingembre, ajouter le canard. "
        "Mijoter longtemps, servir avec le riz."
    ),
    "voanjobory sy henakisoa": (
        "Cuire les pois du cap, ajouter oignon, tomate et ail. "
        "Mijoter et servir avec le riz."
    ),
    "lasopy": "Faire une soupe avec haricots, tomate, oignon, ail et gingembre.",
    "kitoza oeufs riz": (
        "Faire revenir le poulet avec l'oignon, accompagner de riz. "
        "Idéal au petit-déjeuner."
    ),
    "salade pois chiches": (
        "Mélanger pois chiches, tomate et oignon. Assaisonner à l'huile et au sel."
    ),
    "canard aux bredes": (
        "Faire revenir oignon et ail, ajouter le canard puis les brèdes. "
        "Mijoter et servir avec le riz."
    ),
    "vary amin'anana": "Faire revenir oignon, ajouter les brèdes, servir sur riz chaud.",
    "tsaramaso sy henakisoa": "Cuire les haricots, ajouter poulet et tomate, servir avec riz.",
    "akoho gasy": "Mariner le poulet ail-gingembre, braiser avec oignon, servir riz.",
    "soupe tomate ail": "Faire revenir ail et oignon, ajouter tomates, mixer ou écraser.",
    "riz saute legumes": "Faire sauter légumes et oeuf, ajouter riz froid, assaisonner.",
    "haricots coco": "Cuire haricots, ajouter lait de coco et aromates, servir riz.",
    "poisson grille riz": "Griller le poisson citron-ail, accompagner de riz.",
    "omelette tomate": "Battre oeufs, ajouter tomate oignon, cuire à la poêle.",
    "bouillon gingembre": "Infuser gingembre, ajouter citron et miel.",
    "salade tomate oignon": "Couper, assaisonner huile citron sel.",
    "poulet braise rapide": "Saisir poulet, mijoter tomate oignon, servir riz.",
    "ravitoto leger": "Version légère : moins d'arachide, plus de brèdes.",
    "lasopy legume": "Soupe carotte chou tomate, mijoter 20 min.",
    "voanjobory vegetarien": "Pois du cap mijotés tomate ail, sans viande.",
    "patate douce roti": "Couper, huiler, rôtir jusqu'à tendreté.",
    "manioc vapeur arachide": "Cuire manioc vapeur, servir avec arachide concassée.",
    "nouilles oeuf etudiant": "Cuire nouilles, ajouter oeuf brouillé et oignon.",
    "misao legumes": "Sauter légumes, ajouter nouilles, assaisonner.",
    "brochettes poulet": "Embrocher poulet oignon, griller, servir riz.",
    "cresson ail": "Sauter cresson à l'ail rapidement.",
    "aubergine tomate": "Faire revenir aubergine, ajouter sauce tomate, servir riz.",
    "courgette sautee": "Sauter courgette ail, sel.",
    "carotte gingembre": "Sauter carottes avec gingembre.",
    "lentilles tomate": "Cuire lentilles, mijoter tomate ail, servir riz.",
    "pois du cap coco": "Pois du cap au lait de coco, riz.",
    "poulet gingembre rapide": "Saisir poulet gingembre ail, riz.",
    "poisson aigre doux": "Poisson tomate citron, riz.",
    "soupe haricot": "Soupe haricots carotte oignon.",
    "riz jaune etudiant": "Riz sauté tomate oignon coloré.",
    "achard carotte": "Carotte oignon marinés huile gingembre.",
    "varenga leger": "Poulet effiloché plus léger, moins d'huile.",
    "henakisoa sauce tomate": "Poulet mijoté sauce tomate, riz.",
    "canard oignon": "Canard confit oignons, riz.",
    "salade arachide": "Arachides tomate oignon citron.",
    "banane frit riz": "Banane poêlée, riz d'accompagnement.",
    "porridge riz miel": "Riz cuit crémeux, miel et banane.",
    "mais vapeur": "Épis ou grains vapeur, sel léger.",
    "curry pois chiches": "Pois chiches coco tomate, riz.",
    "dal lentilles": "Lentilles épicées gingembre, riz.",
    "wok bredes": "Brèdes sautées ail oignon.",
    "bol pois chiches": "Bol froid pois chiches légumes citron.",
    "bowl riz legumes": "Riz + légumes sautés en bol.",
    "oeufs riz sauce": "Oeufs et riz sauce tomate.",
    "soupe cresson": "Soupe légère au cresson.",
    "poulet citron": "Poulet citronné ail, riz.",
    "haricot carotte": "Haricots mijotés carottes, riz.",
    "poisson tomate rapide": "Poisson sauce tomate express.",
    "chou saute ail": "Chou sauté ail rapide.",
    "riz coco sucré": "Riz au lait de coco miel banane.",
    "lentilles coco": "Lentilles crémeuses coco.",
    "aubergine riz": "Aubergine mijotée tomate sur riz.",
    "patate douce oeuf": "Patate douce rôtie + oeuf.",
    "nouilles poulet": "Nouilles sautées poulet carotte.",
    "salade carotte citron": "Carottes râpées citron.",
    "romazava leger": "Romazava sans riz, plus de brèdes.",
    "pois chiches riz": "Pois chiches simples sur riz.",
}
