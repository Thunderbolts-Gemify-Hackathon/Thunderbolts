# KaliTao

Monorepo KaliTao (hackathon Gemmify, Madagascar) :

- `backend/` — API FastAPI (planning, stock, budget, marchés, Gemma)
- `frontend/` — app Expo / React Native

Aide un foyer à planifier des repas réalistes, suivre le stock, le budget et les points de vente proches.

## Stack

- Python 3.11, FastAPI, SQLAlchemy, SQLite, Pydantic v2
- Expo SDK 54 / React Native
- Ollama en local (Gemma), avec bascule API Gemini si besoin

Variables : voir `.env.example` (`GEMMA4_API_KEY`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `JWT_SECRET`).

## Démarrage rapide (test local)

### Backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m backend.data.seed
pytest -q
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Ollama (optionnel) :

```bash
ollama serve
ollama pull gemma4:latest
python -m backend.scripts.test_ollama
```

### Frontend

```bash
cd frontend
cp .env.example .env   # EXPO_PUBLIC_API_URL=http://IP_LAN:8000
npm install
npx expo start -c
```

Sur téléphone, mets l’IP LAN du Mac dans `frontend/.env`.

### Docker (API seule)

```bash
cp .env.example .env
docker compose up --build
```

API : http://localhost:8000/docs

## Architecture backend

- `routers/` — HTTP
- `services/` — logique métier
- `models/` / `schemas/` — DB et contrats JSON
- `data/` — seed recettes & marchés

**Règle produit** : aucun prix, stock ou distance inventé par le LLM — ces valeurs passent par des outils backend (`logs/tool_calls.log`).

## Routes principales

| Préfixe | Rôle |
|---------|------|
| `/utilisateurs` | Compte, login, JWT |
| `/onboarding` | Profil, foyer, budget, localisation |
| `/stock` | Inventaire, alertes, approvisionnement |
| `/budget` | Contrôle du montant |
| `/market` | Nearby, panier-check, **one-trip** |
| `/planning` | Menus, validation, liste de courses |
| `/courses` | Articles custom |
| `/prices` | Prix crowd |
| `/social` | Défis foyer |
| `/ia` | Chat Gemma, planning, outils |
| `/health` | Santé du service |

## Features à tester en priorité

1. **Connexion JWT** — `/signin` utilise `login-jwt` (access + refresh + api_token).
2. **Un trajet** — Courses → « Un trajet (marchés) » → carte multi-arrêts OSRM → **Sortie marché**.
3. **Sortie marché** — cocher produits, signaler un prix, TTS d’arrêt, terminer → stock.
4. **Défis** — Dashboard → Défis ; valider un repas en cuisine incrémente « 5 repas maison ».
5. **Offline** — couper le réseau, terminer courses / upsert stock → file sync au retour.
6. **Vocal** — « Calcule un trajet pour mes courses » (outil `optimize_one_trip`).

## Tests

```bash
# backend
pytest -q

# frontend typecheck
cd frontend && npx tsc --noEmit
```

CI GitHub Actions : `.github/workflows/ci.yml` (pytest + tsc).

## Parcours produit

Voir `docs/parcours-utilisateur.md`.
