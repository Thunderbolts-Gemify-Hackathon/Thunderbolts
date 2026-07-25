# KaliTao

Backend FastAPI pour KaliTao (hackathon Gemmify).

## Stack

- Python 3.11
- FastAPI + SQLAlchemy + SQLite + Pydantic v2

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn backend.main:app --reload
```

## Architecture

`routers/` appelle `services/`, qui utilise `models/` et `schemas/`.
