from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import budget, gemma, market, onboarding, planning, stock, utilisateur


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="KaliTao API", version="0.1.0", lifespan=lifespan)

# Dev only : Vite + Expo (web / LAN).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?",
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


@app.get("/health")
def health():
    return {"status": "ok", "service": "kalitao"}
