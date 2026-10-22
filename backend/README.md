# CashTrail — Backend

API REST do CashTrail, construída com **FastAPI**, **SQLAlchemy 2.0** e **PostgreSQL**, organizada em vertical slices e testada contra um PostgreSQL real.

Visão geral do produto, ADRs e infraestrutura estão no [README principal](../README.md). Este guia cobre o que é específico do backend: organização do código, configuração, execução, migrações e testes.

---

## Stack

| Responsabilidade | Biblioteca |
|---|---|
| Framework web | FastAPI + Uvicorn |
| ORM e banco | SQLAlchemy 2.0 + psycopg 3 + PostgreSQL 16 |
| Migrações | Alembic |
| Configuração | pydantic-settings (variáveis de ambiente e `.env`) |
| Autenticação | PyJWT + Argon2 (`argon2-cffi`) |
| Rate limiting | slowapi |
| Jobs agendados | APScheduler, dentro do próprio processo da API ([ADR-005](../docs/planning/decisions/ADR-005-apscheduler-over-celery.md)) |
| E-mail | Azure Communication Services (ou console em desenvolvimento) |
| Testes | pytest + httpx + Testcontainers |

Requer **Python 3.12+**.

## Estrutura

```text
backend/
├── src/
│   ├── main.py            # app FastAPI, middlewares, routers e agendador
│   ├── core/              # infraestrutura transversal (sem regra de negócio)
│   │   ├── config.py      # Settings: toda configuração vem daqui
│   │   ├── database.py    # engine, SessionLocal, Base, get_db
│   │   ├── dependencies.py# CurrentUser e proteção CSRF das rotas de cookie
│   │   ├── security.py    # hash de senha e emissão/validação de JWT
│   │   ├── rate_limit.py  # limiter compartilhado
│   │   └── email.py       # backends de e-mail (console / ACS)
│   └── features/          # uma pasta por funcionalidade de negócio
├── alembic/versions/      # migrações versionadas
├── tests/                 # testes transversais (health, e-mail, migrações)
├── conftest.py            # fixtures compartilhadas (Postgres via Testcontainers)
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```

### Slices

| Grupo | Slices |
|---|---|
| Núcleo | `auth`, `accounts`, `categories`, `transactions` |
| Planejamento | `budgets`, `goals`, `recurring`, `commitments`, `transfers` |
| Crédito e dívidas | `credit_cards`, `debts` |
| Patrimônio | `assets`, `investments`, `insurance`, `retirement` |
| Análise | `dashboard`, `reports` (DRE, fluxo de caixa, balanço, CSV), `tax` |
| Entrada de dados | `statement_import` |

## Anatomia de uma slice

Cada slice em `src/features/<nome>/` segue as mesmas camadas:

| Arquivo | Responsabilidade |
|---|---|
| `router.py` | Rotas HTTP: valida a entrada, resolve `CurrentUser`, chama o service e traduz exceções de domínio em status HTTP |
| `schemas.py` | Modelos Pydantic de entrada e saída da API |
| `service.py` | Regras de negócio; é a **única interface pública** da slice para as demais |
| `repository.py` | Consultas SQLAlchemy, sempre filtradas por `user_id` |
| `models.py` | Modelos ORM |
| `tests/` | Testes de API e de regra de negócio da própria slice |

Slices com cálculos mais densos isolam essa lógica em módulos puros, testáveis sem banco: `debts` (cronogramas Price/SAC), `credit_cards` (ciclo da fatura), `investments/position.py` (custo médio e posição), `tax/calc.py` (IRPF) e os módulos de `reports`.

### Regras de dependência

- `transactions` é o núcleo do domínio ([ADR-007](../docs/planning/decisions/ADR-007-vertical-slices-transactions-kernel.md)): as outras slices dependem dela, nunca o contrário.
- Uma slice chama outra **apenas pelo `service`**, nunca pelo `repository`.
- O router nunca acessa o repository diretamente.
- `core/` não contém regra de negócio; a única ponte para `features/` é `dependencies.py`, que carrega o usuário autenticado pela slice `auth`.

O diagrama completo de dependências está em [`09-vertical-slices.md`](../docs/planning/09-vertical-slices.md).

### Autenticação nas rotas

Toda rota protegida depende de `CurrentUser` (`src/core/dependencies.py`), a única implementação da verificação do token. Ela valida o access token e rejeita tokens emitidos antes da última troca de senha.

As rotas que dependem só do cookie de refresh (`/auth/refresh`, `/auth/logout`) exigem também o header `X-Requested-With`, como defesa em profundidade contra CSRF. Login, pedido de recuperação e redefinição de senha são limitados a 5 requisições por minuto por IP.

## Configuração

Toda configuração passa por `src/core/config.py` e pode ser sobrescrita por variável de ambiente (o nome é o mesmo do campo, em maiúsculas) ou pelo arquivo `backend/.env`:

```bash
cp .env.example .env
```

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://cashtrail:cashtrail@localhost:5432/cashtrail` | Conexão com o PostgreSQL. O `.env.example` aponta para o banco do Docker Compose (`localhost:5544`) |
| `JWT_SECRET_KEY` | valor de desenvolvimento | Chave de assinatura dos tokens. **Obrigatório sobrescrever em produção** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Validade do access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Validade do refresh token |
| `COOKIE_SECURE` | `false` | `true` em produção (HTTPS) |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:3000"]` | Origens do frontend, em JSON |
| `ENABLE_SCHEDULER` | `false` | Liga os jobs agendados. Desligado por padrão para que os testes não disparem jobs contra um banco real |
| `FRONTEND_URL` | `http://localhost:3000` | Base do link de recuperação de senha |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | `30` | Validade do link de recuperação |
| `EMAIL_BACKEND` | `console` | `console` escreve o e-mail no log; `acs` envia pelo Azure Communication Services |
| `ACS_CONNECTION_STRING` | vazio | Usado apenas com `EMAIL_BACKEND=acs` |
| `EMAIL_SENDER_ADDRESS` | vazio | Remetente do domínio do ACS |
| `BRAPI_TOKEN` | vazio | Token da brapi; sem ele, só ativos de teste têm cotação |
| `QUOTES_MONTHLY_CAP` | `10000` | Teto mensal de requisições à brapi |
| `APP_VERSION` | `dev` | Exposto em `/health`; o deploy injeta o SHA do commit |

> Nunca coloque credenciais de produção no `.env` local. Se o seu `.env` apontar para um banco remoto, sobrescreva `DATABASE_URL` antes de rodar migrações ou a API.

## Executando

### Com Docker Compose (recomendado)

Na raiz do repositório:

```bash
docker compose up -d
```

| Serviço | Endereço |
|---|---|
| API | `http://localhost:8001` |
| Documentação interativa (Swagger) | `http://localhost:8001/docs` |
| Health check | `http://localhost:8001/health` |
| PostgreSQL | `localhost:5544` (usuário, senha e banco: `cashtrail`) |

O container aplica as migrações (`alembic upgrade head`) antes de subir a API, e o código é montado como volume. As portas foram remapeadas (5432 → 5544, 8000 → 8001) para evitar conflito com serviços locais; ajuste o `docker-compose.yml` se necessário.

### Fora do Docker

Útil para depurar. Suba só o banco e rode a API num ambiente virtual:

```bash
docker compose up -d db

cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env

alembic upgrade head
uvicorn src.main:app --reload --port 8001
```

Se o container `backend` do Compose estiver rodando, pare-o antes (`docker compose stop backend`) ou use outra porta e ajuste `NEXT_PUBLIC_API_URL` no frontend.

## Migrações

As migrações ficam em `alembic/versions/` e leem a conexão de `DATABASE_URL`.

```bash
alembic upgrade head                                   # aplica todas
alembic revision --autogenerate -m "descricao curta"   # gera a partir dos models
alembic downgrade -1                                   # desfaz a última
```

Revise sempre o arquivo gerado pelo `--autogenerate`: ele não detecta tudo (por exemplo, alterações em valores de enum). Ao criar um model novo, importe-o também no `conftest.py` para que a suíte de testes crie a tabela.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Os testes de integração sobem um **PostgreSQL 16 real** com Testcontainers, então é preciso ter o Docker em execução. A suíte não depende de mocks de banco.

| Onde | O que cobre |
|---|---|
| `src/features/<slice>/tests/` | API e regras de negócio de cada slice, incluindo o isolamento entre usuários (`test_user_cannot_access_another_users_*`) |
| `tests/test_migrations.py` | Aplica as migrações do Alembic num banco vazio e verifica que o schema resultante funciona |
| `tests/test_health.py`, `tests/test_email.py` | Health check e backends de e-mail |

Como funcionam as fixtures (`conftest.py`):

- Um container PostgreSQL é criado **uma vez por sessão**, e as tabelas são criadas a partir de `Base.metadata`.
- Cada teste recebe uma sessão isolada (`db_session`), desfeita ao final, e um `client` (`TestClient`) com `get_db` sobrescrito para usar essa sessão.
- O rate limiting é desligado durante os testes, para que logins repetidos não esbarrem no limite.

Comandos úteis:

```bash
pytest src/features/credit_cards     # uma slice
pytest -k another_users              # por nome (ex.: testes de isolamento)
pytest -q -x                         # para no primeiro erro
```

## Jobs agendados

Com `ENABLE_SCHEDULER=true`, o APScheduler roda dentro do processo da API:

| Job | Frequência | O que faz |
|---|---|---|
| Recorrências | Na subida e a cada 24h | Gera os lançamentos e contas a pagar recorrentes vencidos e avança a próxima ocorrência |
| Cotações | Na subida (em segundo plano) e a cada 24h | Atualiza as cotações da carteira de todos os usuários, respeitando o teto mensal e pulando cotações com menos de 4h |

Os jobs também rodam na subida porque o Container App escala a zero quando ocioso, e o intervalo de 24h raramente chegaria a completar. Falhas da fonte de cotações são isoladas e não derrubam a API.

## Deploy

A imagem é construída a partir do `Dockerfile` e publicada pelo workflow [`deploy.yml`](../.github/workflows/deploy.yml), descrito no [README principal](../README.md#cicd-e-infraestrutura).

O container executa `alembic upgrade head` antes de iniciar o Uvicorn, então o banco não precisa ficar exposto ao runner do GitHub. Isso é seguro enquanto o Container App tiver **no máximo uma réplica**; com mais réplicas, as migrações precisam sair da inicialização.

## Referências

- [Arquitetura](../docs/planning/08-architecture.md) e [vertical slices](../docs/planning/09-vertical-slices.md)
- [Modelo de dados](../docs/planning/10-data-model.md)
- [Segurança](../docs/planning/11-security.md)
- [Stack e justificativas](../docs/planning/07-stack.md)
