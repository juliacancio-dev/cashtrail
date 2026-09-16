from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cashtrail:cashtrail@localhost:5432/cashtrail"

    # ADR-006: refresh token em cookie httpOnly, access token só em memória no cliente.
    # jwt_secret_key tem valor padrão só para dev local — em produção vem do Azure Key Vault (SEC-005).
    jwt_secret_key: str = "dev-secret-change-me-32-bytes-minimum!!"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    # Secure=False por padrão porque dev local roda em HTTP; produção (Azure, HTTPS) deve
    # sobrescrever via env var COOKIE_SECURE=true.
    cookie_secure: bool = False

    # Marco 2: origem do frontend local por padrão; sobrescrever via env em produção.
    cors_allowed_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
