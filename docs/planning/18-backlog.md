# CashTrail — Backlog Inicial (FASE 18)

> Estrutura: Epic → Feature → Vertical Slice → Task. Detalhado o suficiente pra orientar a implementação, sem virar documentação artificial (tasks de código-fonte específicas serão quebradas na hora de cada slice, não aqui).

## Epic 1 — Fundação (Marco 1)
- **Feature**: Scaffold do monorepo
  - Task: estrutura `backend/`, `frontend/`, `docs/`, `.github/workflows/`
  - Task: Docker Compose com Postgres local
  - Task: esqueleto FastAPI com `/health`
  - Task: esqueleto Next.js + shadcn/ui configurado
  - Task: CI (GitHub Actions) rodando build
  - **Critério de aceitação**: `docker-compose up` funciona; CI verde. **Risco**: nenhum relevante (R-register não lista risco pra este marco).

## Epic 2 — Primeira Vertical Slice + Deploy (Marco 2)
- **Feature**: Autenticação (`auth`) — RF-001, RF-002, RNF-001/002, SEC-001/002/006
  - Vertical Slice: registro de usuário
  - Vertical Slice: login com JWT (access em memória + refresh em cookie `httpOnly`, ADR-006)
  - Task: teste dedicado de isolamento por usuário (RNF-001)
  - **Dependências**: Epic 1. **Risco**: R-008 (auth própria).
- **Feature**: Contas (`accounts`) — RF-003
  - Vertical Slice: CRUD de conta
  - **Dependências**: `auth`.
- **Feature**: Deploy real na Azure
  - Task: SPIKE Next.js em Static Web Apps (decide fallback Vercel) — R-002
  - Task: provisionar Container Apps + Postgres Flexible Server + Key Vault
  - Task: configurar CORS + cookie cross-origin (ADR-006)
  - **Critério de aceitação**: fluxo registro→login→criar conta funciona na URL pública. **Riscos**: R-002, R-003.

## Epic 3 — Núcleo do MVP (Marco 3)
- **Feature**: Categorias (`categories`) — RF-004
- **Feature**: Lançamentos (`transactions`) — RF-005
  - Task: modelo de dados conforme `10-data-model.md` (invariante `amount > 0`, `type` define direção)
- **Feature**: Dashboard (`dashboard`) — RF-006
  - Task: agregação por categoria/mês
  - Task: gráficos (Recharts) no frontend
  - **Dependências**: Epic 2. **Critério de aceitação**: dashboard bate com soma manual.

## Epic 4 — Orçamento e Metas (Marco 4)
- **Feature**: Orçamento (`budgets`) — RF-007, RF-008
  - Task: unique constraint (`user_id`, `category_id`, `month`) — RB-002
  - Task: alerta in-app quando estourado (decisão `12-mvp.md`)
- **Feature**: Metas (`goals`) — RF-009
  - Task: vínculo lançamento↔meta (1:1, decisão `04-usecases.md`)
  - Task: cálculo de progresso derivado (RB-003)
  - **Dependências**: Epic 3.

## Epic 5 — Recorrência (Marco 5)
- **Feature**: Lançamentos recorrentes (`recurring`) — RF-010
  - Task: modelo `RecurringTransaction` + job APScheduler (ADR-005)
  - Task: geração de `Transaction` com `source=recurring`, nunca inserção direta (regra de `09-vertical-slices.md`)
  - **Dependências**: Epic 3. **Risco**: dificuldade de testar job agendado (`14-estimates.md`).

## Epic 6 — Hardening do MVP (Marco 6)
- Task: cobertura de teste revisada em todos os fluxos críticos
- Task: aplicar checklist de segurança (`11-security.md`)
- Task: automação de start/stop do banco (R-004)
- Task: confirmar política de backup do Postgres (R-009)
- Task: README final com arquitetura, decisões e link de demo
- **Dependências**: Epics 3, 4, 5. **Critério de aceitação**: MVP atende `12-mvp.md`.

## Epic 7 — MVP+1 (Marco 7)
- **Feature**: Importação de extrato (`statement_import`) — RF-011, RF-012
  - Task: validar formato real do extrato com arquivo de exemplo (R-007) **antes** de implementar o parser
  - Task: parser CSV + parser OFX (usar `FITID` quando disponível, ADR/heurística de `04-usecases.md`)
  - Task: tela de revisão de possíveis duplicatas (R-006)
- **Feature**: Recuperação de senha — RF-013
  - Task: integração com Azure Communication Services Email
  - Task: token de uso único com expiração curta
  - **Dependências**: Epic 6 (MVP completo).

## Epic 8 — Evolução/Stretch (Marco 8, não comprometido)
- Terraform para infraestrutura Azure
- Observabilidade (Application Insights ou similar)
- MFA
- Reavaliar Open Finance real (baixíssima prioridade, ver R-010)

---

**STATUS**: Pronto para avançar.
