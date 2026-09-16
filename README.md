# CashTrail

Plataforma de gestão financeira pessoal — projeto pessoal com uso real, construído com discovery, arquitetura e decisões documentadas do zero.

## Stack

- **Backend**: Python + FastAPI + SQLAlchemy 2.0 + PostgreSQL
- **Frontend**: Next.js (App Router) + shadcn/ui + Tailwind CSS
- **Infra**: Azure (Container Apps, Static Web Apps, PostgreSQL Flexible Server)
- **CI/CD**: GitHub Actions

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

## Documentação do projeto

Todo o discovery — problema, requisitos, arquitetura, decisões técnicas (ADRs), roadmap e backlog — está em [`docs/planning/`](docs/planning/), começando por [`00-project-brief.md`](docs/planning/00-project-brief.md).
