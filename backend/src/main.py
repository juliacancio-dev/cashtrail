from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.core.config import settings
from src.core.database import SessionLocal
from src.core.rate_limit import limiter
from src.features.accounts.router import router as accounts_router
from src.features.auth.router import router as auth_router
from src.features.budgets.router import router as budgets_router
from src.features.categories.router import router as categories_router
from src.features.dashboard.router import router as dashboard_router
from src.features.goals.router import router as goals_router
from src.features.recurring import service as recurring_service
from src.features.recurring.router import router as recurring_router
from src.features.transactions.router import router as transactions_router


def _run_recurring_job() -> None:
    """ADR-005: APScheduler roda dentro do processo da API, sem worker dedicado."""
    db = SessionLocal()
    try:
        recurring_service.generate_due_transactions(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    if settings.enable_scheduler:
        # Roda uma vez já na subida: o Container App escala a zero quando ocioso
        # (05-integrations.md), então esperar 24h pelo primeiro `interval` deixaria
        # recorrências vencidas esperando o próximo acesso à API por muito tempo.
        _run_recurring_job()
        scheduler.add_job(_run_recurring_job, "interval", days=1, id="generate_recurring_transactions")
        scheduler.start()
    yield
    if settings.enable_scheduler:
        scheduler.shutdown()


app = FastAPI(title="CashTrail API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(dashboard_router)
app.include_router(goals_router)
app.include_router(budgets_router)
app.include_router(recurring_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
