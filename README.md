# KaliTao

Backend FastAPI pour KaliTao (hackathon Gemmify, Madagascar).
Aide un foyer à planifier des repas réalistes, suivre le stock, le budget et les points de vente proches.

## Stack

- Python 3.11
- FastAPI, SQLAlchemy, SQLite, Pydantic v2
- Ollama en local (modèle Gemma), avec bascule API Gemini si besoin
- Variable d’environnement : voir `.env.example` (`GEMMA4_API_KEY`, `OLLAMA_HOST`)

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest -q
uvicorn backend.main:app
```

Pour Ollama (optionnel en local) :

```bash
ollama serve
ollama pull gemma4:e2b
python -m backend.scripts.test_ollama
```

## Architecture

`routers/` expose le HTTP.  
`services/` porte la logique métier (réutilisable hors API).  
`models/` et `schemas/` décrivent la base et les contrats JSON.  
`data/` contient le seed (recettes, marchés).

Services utiles côté planification :

- `recipe_rag` : filtre les recettes (allergies, tabous, tags, objectif)
- `prompts` : construit le contexte foyer pour Gemma
- `gemma_client` / `gemma_agent` / `gemma_tools` : appel modèle, boucle d’outils, exécution réelle (`check_budget`, `find_nearby_market`, `check_expiry`, `update_stock`)
- `planning_generation_service` : enchaîne profil → recettes → Gemma → persistance

Règle produit : aucun prix, stock ou distance inventé. Ces valeurs passent toujours par un outil backend, journalisé dans `logs/tool_calls.log`.

## Routes principales

- `/onboarding/...` : profil, foyer, préférences, budget, localisation
- `/stock/...` : inventaire et alertes de péremption
- `/budget/...` : contrôle du montant disponible
- `/market/...` : points de vente et prix
- `/planning/...` : planning de repas et validation
- `/health` : état du service

## Tests

```bash
pytest -q
python -m backend.scripts.test_flow_complet
```
