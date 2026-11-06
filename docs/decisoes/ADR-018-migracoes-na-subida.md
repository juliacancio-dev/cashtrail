# ADR-018 — Migrações aplicadas na subida do container

- **Status:** Aceita
- **Data:** 2026-09-28
- **Contexto de origem:** deploy automatizado do MVP (workflow `deploy.yml`)

## Contexto e problema

As migrações do Alembic precisam rodar contra o banco de produção a cada deploy. O banco não deve ficar exposto ao runner do GitHub Actions.

## Opções consideradas

1. **Passo de migração no workflow**, com o runner conectando no banco.
2. **Job separado** (Container Apps Job) que roda as migrações antes da troca de revisão.
3. **Na subida do container:** `alembic upgrade head && exec uvicorn ...` no `Dockerfile`.

## Decisão

Escolhida: **na subida do container**, porque não exige abrir o banco para o runner nem manter um recurso a mais, e o deploy só é considerado concluído quando o `/health` da nova revisão devolve o SHA do commit.

## Consequências

- **Positivas:** um caminho só; se uma migração falhar, o container não sobe, o `/health` nunca devolve o SHA novo e o deploy falha com mensagem clara.
- **Negativas:** **seguro só com no máximo uma réplica.** Com mais réplicas, duas poderiam migrar ao mesmo tempo, e as migrações precisam sair da inicialização (opção 2).
- **Revisar se:** o backend precisar escalar para mais de uma réplica.

## Mais informações

- [Deploy e operação](../guias/deploy-e-operacao.md) e [Migrações](../arquitetura/modelo-de-dados.md#migrações).
