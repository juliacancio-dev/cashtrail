# ADR-005 — APScheduler (não Celery + Redis) para lançamentos recorrentes

**Status**: Aceito

**Contexto**: geração automática de lançamentos recorrentes precisa de um job periódico.

**Alternativas**: APScheduler (roda dentro do processo da API) vs. Celery + Redis (fila/worker dedicados).

**Decisão**: APScheduler.

**Justificativa**: o projeto tem exatamente um job periódico — Celery+Redis adicionaria um serviço a mais pra manter, testar e pagar na Azure, sem necessidade concreta proporcional ao problema.

**Consequências**: mais simples de operar e mais barato; se o projeto no futuro precisar de múltiplos jobs assíncronos pesados, essa decisão deve ser revisitada.
