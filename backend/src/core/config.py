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

    # Marco 5: desligado por padrão de propósito — o job usa SessionLocal (bound ao
    # DATABASE_URL real), não o get_db override dos testes; se ligado por padrão,
    # TestClient(app) dispararia o job contra o banco de verdade a cada teste.
    # Produção liga via env var ENABLE_SCHEDULER=true.
    enable_scheduler: bool = False

    # SHA do commit, injetado pelo deploy.yml. Exposto no /health para o deploy
    # confirmar que a revisão nova está no ar (ambiente Express não expõe
    # nome/estado de revisão de forma confiável).
    app_version: str = "dev"

    # Marco 7 (RF-013): recuperação de senha.
    password_reset_token_expire_minutes: int = 30
    # Base do link enviado por e-mail; produção sobrescreve via FRONTEND_URL (deploy.yml).
    frontend_url: str = "http://localhost:3000"
    # "console" só registra o e-mail no log (dev e enquanto o Azure Communication
    # Services não estiver configurado); "acs" envia de verdade (produção).
    email_backend: str = "console"
    # Só usados com EMAIL_BACKEND=acs. A connection string é segredo: no Container App
    # entra como secret (secretref), nunca em texto puro (SEC-005).
    acs_connection_string: str = ""
    # Remetente do domínio do Communication Services, ex: DoNotReply@<id>.azurecomm.net
    email_sender_address: str = ""


    # Marco 13 (decisão 2): cotações de renda variável. O token é segredo (SEC-005): só no backend,
    # em variável de ambiente; vazio = a brapi atende só ativos de teste (PETR4, VALE3, MGLU3, ITUB4).
    brapi_base_url: str = "https://brapi.dev"
    brapi_token: str = ""
    # Teto mensal de requisições à fonte (o plano grátis permite 15.000); margem de segurança.
    quotes_monthly_cap: int = 10000

settings = Settings()
