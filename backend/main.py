from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import init_db
from backend.routers import budget, gemma, market, onboarding, planning, stock


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="KaliTao API", version="0.1.0", lifespan=lifespan)

# Routers = HTTP only. La logique métier est dans services/ (réutilisable hors API).
app.include_router(onboarding.router)
app.include_router(stock.router)
app.include_router(budget.router)
app.include_router(market.router)
app.include_router(planning.router)
app.include_router(gemma.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "kalitao"}
