from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import (
    budget,
    gemma,
    ingredient,
    market,
    onboarding,
    planning,
    stock,
    utilisateur,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="KaliTao API", version="0.1.0", lifespan=lifespan)

# Dev only : autorise le frontend local (Vite) à appeler l'API depuis un autre port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers = HTTP only. La logique métier est dans services/ (réutilisable hors API).
app.include_router(onboarding.router)
app.include_router(stock.router)
app.include_router(budget.router)
app.include_router(market.router)
app.include_router(planning.router)
app.include_router(gemma.router)
app.include_router(utilisateur.router)
app.include_router(ingredient.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "kalitao"}
