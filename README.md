# CashTrail

Plataforma de gestão financeira pessoal — projeto pessoal com uso real, construído com discovery, arquitetura e decisões documentadas do zero.

## O problema

Controle financeiro pessoal espalhado entre planilhas e memória: nenhuma visão estruturada de pra onde o dinheiro vai, se o orçamento do mês estourou, ou se uma meta de economia está indo bem. O discovery completo (dores, pesquisa de mercado, requisitos) está em [`docs/planning/`](docs/planning/).

## Funcionalidades do MVP

| Funcionalidade | Regra de negócio principal |
|---|---|
| Autenticação (registro/login) | JWT com access token em memória + refresh token em cookie `httpOnly` |
| Contas | Conta arquivada não aceita novos lançamentos, mas mantém histórico |
| Categorias | Categoria com lançamentos associados não pode ser excluída, só arquivada |
| Lançamentos | Pertence a exatamente uma conta e uma categoria do próprio usuário; `amount` sempre positivo, direção vem do `type` |
| Dashboard | Resumo, gasto por categoria e evolução de saldo — soma bate com conferência manual |
| Orçamento | Um orçamento por categoria/mês; alerta in-app quando ultrapassado |
| Metas de economia | Progresso = soma dos lançamentos vinculados; marcada como atingida automaticamente |
| Lançamentos recorrentes | Job agendado gera o lançamento e avança a próxima ocorrência, sem ação manual |

Importação de extrato (CSV/OFX) e recuperação de senha ficam para depois do MVP (`docs/planning/12-mvp.md`).

## Arquitetura

**Vertical slices**: cada funcionalidade (`accounts`, `categories`, `transactions`, `dashboard`, `budgets`, `goals`, `recurring`) é uma fatia completa — schema, regra de negócio, persistência, rota e teste moram juntos em `backend/src/features/<nome>/`. `transactions` é o núcleo do domínio: as demais slices dependem dela (nunca o contrário), chamando só sua camada `service` pública — nunca o `repository`/model ORM de outra slice diretamente. Detalhes e diagrama de dependências em [`docs/planning/09-vertical-slices.md`](docs/planning/09-vertical-slices.md).

**Decisões de maior consequência** (ADRs completos em [`docs/planning/decisions/`](docs/planning/decisions/)):
- Azure como provedor de nuvem (ADR-001), multiusuário desde o início mesmo sendo uso pessoal (ADR-002)
- SQLAlchemy puro em vez de SQLModel (ADR-003), auth implementada na mão em vez de biblioteca pronta (ADR-004)
- JWT com refresh em cookie `httpOnly` + access token só em memória, nunca em `localStorage` (ADR-006) — elimina roubo de token via XSS
- APScheduler (não Celery+Redis) para o job de lançamentos recorrentes (ADR-005) — um único job periódico não justifica infraestrutura de fila dedicada
- Vertical slices com `transactions` como núcleo desacoplado (ADR-007)

**Infra**: Azure Container Apps para backend e frontend (o frontend usa static export do Next.js, servido por nginx no mesmo tipo de recurso — Static Web Apps foi abandonado por bloqueio de política de região na subscription Azure for Students), PostgreSQL Flexible Server, Azure Container Registry.

## Segurança

Threat model completo em [`docs/planning/11-security.md`](docs/planning/11-security.md). Controles em vigor:
- Toda query filtra por `user_id` do token autenticado (RNF-001/SEC-002) — testado em cada slice (`test_user_cannot_access_another_users_*`)
- Rate limiting no login (SEC-006, 5 tentativas/minuto)
- CSRF: `SameSite=Strict` no cookie de refresh + header customizado exigido nas rotas que dependem só do cookie (`/auth/refresh`, `/auth/logout`)
- Segredos fora do código-fonte (Azure Key Vault / variáveis de ambiente)
- SQL injection: SQLAlchemy ORM exclusivamente, sem SQL concatenado

## Stack

- **Backend**: Python + FastAPI + SQLAlchemy 2.0 + PostgreSQL + Alembic + APScheduler
- **Frontend**: Next.js (App Router, static export) + shadcn/ui + Tailwind CSS + Recharts
- **Infra**: Azure (Container Apps, PostgreSQL Flexible Server, Container Registry)
- **CI/CD**: GitHub Actions (testes de backend/frontend a cada push; start/stop agendado do banco)

## Como rodar localmente

```bash
docker compose up -d
```

- Backend: http://localhost:8001/health
- Postgres: `localhost:5544` (usuário/senha/db: `cashtrail`)

> Nota: as portas padrão (5432, 8000) foram remapeadas porque já havia um PostgreSQL nativo do Windows e uma reserva de porta do sistema usando-as nesta máquina. Ajuste `docker-compose.yml`/`.env` se seu ambiente for diferente.

Frontend (fora do Docker Compose por enquanto):

```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Testes de integração usam Testcontainers (Postgres real via Docker), não mocks — cobrem os fluxos críticos: autenticação, isolamento por usuário em toda slice, RB-001 a RB-004, rate limiting e CSRF.

## Status

MVP (Marcos 1-6 do roadmap, ver [`docs/planning/13-roadmap.md`](docs/planning/13-roadmap.md)) implementado e testado localmente ponta a ponta. Deploy em produção no Azure: backend e frontend do Marco 2 já validados ao vivo; Marcos 3-6 aguardando um próximo deploy em lote (link de demo será adicionado aqui quando isso acontecer).

## Documentação do projeto

Todo o discovery — problema, requisitos, arquitetura, decisões técnicas (ADRs), roadmap e backlog — está em [`docs/planning/`](docs/planning/), começando por [`00-project-brief.md`](docs/planning/00-project-brief.md).
