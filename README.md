# Kaly'Tao

Monorepo Kaly'Tao (hackathon Gemmify, Madagascar) :

- `backend/` : API FastAPI (planning, stock, budget, marchés, Gemma)
- `frontend/` : app Expo / React Native

Backend FastAPI pour KaliTao (hackathon Gemmify, Madagascar).
Aide un foyer à planifier des repas réalistes, suivre le stock, le budget et les points de vente proches.

## Stack

- Python 3.11, FastAPI, SQLAlchemy, SQLite, Pydantic v2
- Expo SDK 54, React Native
- Ollama en local (modèle Gemma), avec bascule API Gemini si besoin
- Python 3.11
- FastAPI, SQLAlchemy, SQLite, Pydantic v2
- Ollama en local (modèle Gemma), avec bascule API Gemini si besoin
- Variable d’environnement : voir `.env.example` (`GEMMA4_API_KEY`, `OLLAMA_HOST`)

## Backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m backend.data.seed
pytest -q
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Variables : voir `.env.example` (`GEMMA4_API_KEY`, `OLLAMA_HOST`, `OLLAMA_MODEL`).

Ollama (optionnel) :

```bash
ollama serve
ollama pull gemma4:latest
python -m backend.scripts.test_ollama
```

## Frontend

```bash
cd frontend
cp .env.example .env
npm install
npx expo start -c
pytest -q
uvicorn backend.main:app
```

Pour Ollama (optionnel en local) :

```bash
ollama serve
ollama pull gemma4:e2b
python -m backend.scripts.test_ollama
```

Sur téléphone, mets l’IP LAN du Mac dans `frontend/.env` :

```env
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000
```

## Architecture backend

`routers/` expose le HTTP.  
`services/` porte la logique métier.  
`models/` et `schemas/` décrivent la base et les contrats JSON.  
`data/` contient le seed (recettes, marchés).

Règle produit : aucun prix, stock ou distance inventé. Ces valeurs passent toujours par un outil backend.

## Routes principales

- `/onboarding/...` : profil, foyer, préférences, budget, localisation, état du jour
- `/stock/...` : inventaire
- `/budget/...` : contrôle du montant disponible
- `/market/...` : points de vente et prix (seed)
- `/planning/...` : planning de repas, validation, liste de courses par période
- `/ia/...` : génération planning, chat Gemma, directive courses, suggestion remède
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
# backend
pytest -q

# frontend (typecheck)
cd frontend && npx tsc --noEmit
pytest -q
python -m backend.scripts.test_flow_complet
```
