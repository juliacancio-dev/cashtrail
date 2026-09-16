# CashTrail — Checkpoint dos Gates (FASE 24 da metodologia)

## GATE 1 — Problema
**Temos clareza suficiente sobre o problema, usuário e objetivo?** ✅ Sim.
Duplo problema mapeado (portfólio + controle financeiro real), usuária única confirmada, dores validadas por ela mesma (`01-discovery.md`).

## GATE 2 — Solução
**Temos uma solução plausível e um MVP definido?** ✅ Sim.
8 funcionalidades obrigatórias definidas e justificadas contra as 4 dores confirmadas (`12-mvp.md`).

## GATE 3 — Viabilidade
**Pesquisamos APIs, serviços, custos, limitações e riscos técnicos?** ✅ Sim.
Mercado (`02-market-research.md`), serviços Azure (`05-integrations.md`), custos com cenários (`06-costs.md`), Risk Register (`15-risks.md`) — incluindo o achado crítico de que o banco de dados sozinho pode estourar o crédito estudantil se ficar sempre ligado.

## GATE 4 — Arquitetura
**Temos arquitetura, domínio, dados, integrações e Vertical Slices definidos?** ✅ Sim.
Arquitetura (`08-architecture.md`), Vertical Slices (`09-vertical-slices.md`), modelo de dados (`10-data-model.md`), segurança (`11-security.md`), 7 ADRs registrando as decisões de maior consequência.

## GATE 5 — Execução
**Temos backlog inicial, estimativas, primeira slice e critérios de aceitação?** ✅ Sim.
Roadmap com 8 marcos (`13-roadmap.md`), estimativas em intervalos (`14-estimates.md`), backlog por Epic/Feature/Slice (`18-backlog.md`), traceabilidade completa (`17-traceability.md`), Definition of Ready/Done (`19-definition-ready-done.md`).

---

## Todos os 5 gates aprovados.

**Primeira Vertical Slice a implementar**: **Marco 1 (Fundação)**, seguido imediatamente do **Marco 2** — `auth` (registro/login) + `accounts` (CRUD simples), atravessando toda a arquitetura até deploy real na Azure. Essa é a fatia que valida se tudo que foi decidido neste discovery realmente funciona na prática (SPIKE do frontend, cookie cross-origin, cold start).

**Pendências que seguem junto pra implementação (não bloqueiam o início, mas devem ser resolvidas nos primeiros marcos)**:
- SPIKE Next.js em Azure Static Web Apps (Marco 2)
- Formato real do extrato bancário — validar com arquivo de exemplo (antes do Marco 7)
- Política de backup do Postgres — confirmar no portal Azure (Marco 6)

---

## Resumo de todo o discovery (`docs/planning/`)

| # | Documento | Fase |
|---|---|---|
| 00 | project-brief.md | Resumo executivo |
| 01 | discovery.md | FASE 0-1 |
| 02 | market-research.md | FASE 2 |
| 03 | requirements.md | FASE 3 |
| 04 | usecases.md | FASE 4 |
| 05 | integrations.md | FASE 5 |
| 06 | costs.md | FASE 6 |
| 07 | stack.md | FASE 7 |
| 08 | architecture.md | FASE 8 |
| 09 | vertical-slices.md | FASE 9 |
| 10 | data-model.md | FASE 10 |
| 11 | security.md | FASE 11 |
| 12 | mvp.md | FASE 12 |
| 13 | roadmap.md | FASE 13 |
| 14 | estimates.md | FASE 14 |
| 15 | risks.md | FASE 15 |
| decisions/ADR-001 a 007 | | Registros de decisão arquitetural |
| 17 | traceability.md | FASE 17 |
| 18 | backlog.md | FASE 18 |
| 19 | definition-ready-done.md | DoR/DoD |
| 20 | gates-checkpoint.md | Gates finais |

**Discovery completo.** Pronto pra começar a implementação pelo Marco 1 quando você quiser.
