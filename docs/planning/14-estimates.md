# CashTrail — Estimativa de Esforço e Tempo (FASE 14)

> **Esforço** = quantidade de trabalho (horas), independente de quando é feito.
> **Tempo de calendário** = quando isso realmente vai acontecer, considerando sua disponibilidade real.
> Premissa de capacidade: **3-6h/semana** (você trabalha full-time na Greystar; CashTrail é feito nas horas livres).

## Estimativa por marco

| Marco | Esforço (h) | Confiança | Premissas | Risco que pode inflar a estimativa |
|---|---|---|---|---|
| 1 — Fundação | 4-8h | Alta | Sem obstáculo de tooling incomum; stack já decidida em `07-stack.md` | Baixo — é a parte mais mecânica do projeto |
| 2 — 1ª Vertical Slice + deploy real | 16-30h | **Média-baixa** | Primeiro contato real com provisionamento Azure (Container Apps, Postgres Flexible Server, Static Web Apps/Vercel, CORS, Key Vault) | **Maior risco do roadmap**: se o SPIKE do Next.js no Static Web Apps falhar (migrar pra Vercel) ou o cookie `httpOnly` cross-origin der trabalho de configurar, pode somar +4-10h não planejadas |
| 3 — Categorias/Lançamentos/Dashboard | 16-28h | Média-alta | Padrão de slice já validado no Marco 2, replicação é mais previsível | Cálculo de agregações do dashboard (gráficos com Recharts) é a parte mais imprevisível aqui |
| 4 — Orçamento e Metas | 14-22h | Média-alta | Depende só de `transactions`, já maduro | Vínculo lançamento↔meta (UI de seleção) pode exigir mais iteração de UX do que o esperado |
| 5 — Recorrência | 10-16h | Média | Job periódico único, sem infra extra (APScheduler) | Testar geração agendada de forma automatizada é historicamente mais chato do que parece (mock de tempo/data) |
| 6 — Hardening do MVP | 10-18h | Média | Checklist de segurança e teste já mapeados em `11-security.md`/`03-requirements.md` | Automação de start/stop do banco (`06-costs.md`) é a peça menos explorada até aqui |
| **Total até o fim do MVP (Marcos 1-6)** | **70-122h** | Média | Soma direta dos marcos acima, sem folga extra | Ver "Caminho crítico" abaixo |
| 7 — MVP+1 (import + recuperação de senha) | 22-38h | Média | Import CSV/OFX é a parte mais complexa isolada do projeto inteiro | Parsing de OFX real pode ter variações entre bancos não previstas na especificação do formato |

## Conversão para tempo de calendário (3-6h/semana)

| Marco | Semanas estimadas |
|---|---|
| 1 | 1-3 semanas |
| 2 | 3-10 semanas |
| 3 | 3-9 semanas |
| 4 | 2-7 semanas |
| 5 | 2-5 semanas |
| 6 | 2-6 semanas |
| **MVP completo (1-6)** | **~13-40 semanas (≈ 3-9 meses)** |
| 7 (MVP+1) | mais ~4-13 semanas (≈ 1-3 meses) |

**Por que o intervalo é tão largo**: a diferença entre 3h/semana e 6h/semana já dobra o tempo de calendário sozinha; somado à incerteza técnica real do Marco 2 (caminho crítico), um intervalo estreito seria falsa precisão. Prefiro um número honesto e largo a um número "bonito" e errado.

## Caminho crítico

**Marco 2** é o caminho crítico do projeto — não pelo volume de horas, mas porque:
1. Todos os marcos seguintes (3, 4, 5) **dependem do padrão de deploy e autenticação validado nele** (`13-roadmap.md`).
2. Concentra as 3 maiores incertezas técnicas ainda não resolvidas: SPIKE do frontend, cookie cross-origin, cold start do Container Apps.
3. É a primeira vez lidando com provisionamento real na Azure para este projeto — mesmo com experiência prévia em nuvem, cada conta/projeto novo costuma ter atrito de configuração específico.

**Recomendação prática**: não subestimar o Marco 2 mentalmente só porque o escopo de funcionalidade (auth + accounts) parece pequeno — o "tamanho" dele está na incerteza técnica, não na quantidade de código.

## O que pode aumentar a estimativa significativamente

- SPIKE do Static Web Apps falhar → migração pra Vercel no meio do Marco 2 (+4-10h).
- Cold start do Container Apps ser inaceitável na prática → precisar reavaliar App Service (`05-integrations.md`), o que reabriria uma decisão já fechada (+tempo de retrabalho, não quantificável agora).
- Formato real do extrato bancário (CSV/OFX) ser mais irregular do que o esperado no Marco 7 (pendência já registrada em `04-usecases.md`).

---

**STATUS**: Pronto para avançar.

Seguimos para a **FASE 15 — Riscos e Dependências** (Risk Register formal, consolidando tudo que já foi identificado nas fases anteriores)?
