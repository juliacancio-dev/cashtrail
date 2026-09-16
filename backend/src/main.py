from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.features.accounts.router import router as accounts_router
from src.features.auth.router import router as auth_router

app = FastAPI(title="CashTrail API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(accounts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
