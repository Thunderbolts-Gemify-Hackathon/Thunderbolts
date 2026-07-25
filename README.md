# KaliTao

Monorepo KaliTao (hackathon Gemmify, Madagascar) :

- `backend/` : API FastAPI (planning, stock, budget, marchés, Gemma)
- `frontend/` : app Expo / React Native

Aide un foyer à planifier des repas réalistes, suivre le stock, le budget et les points de vente proches.

## Stack

- Python 3.11, FastAPI, SQLAlchemy, SQLite, Pydantic v2
- Expo SDK 54, React Native
- Ollama en local (modèle Gemma), avec bascule API Gemini si besoin

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
- `/planning/...` : planning de repas et validation
- `/ia/...` : génération planning, chat Gemma, directive courses, suggestion remède
- `/health` : état du service

## Tests

```bash
# backend
pytest -q

# frontend (typecheck)
cd frontend && npx tsc --noEmit
```
