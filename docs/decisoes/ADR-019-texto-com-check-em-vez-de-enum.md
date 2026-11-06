# ADR-019 — Texto com `CHECK` em vez de enum nativo para valores novos

- **Status:** Aceita
- **Data:** 2026-10-08

## Contexto e problema

Os primeiros conjuntos de valores (`account_type`, `transaction_type`, `transaction_source`, `recurring_frequency`) viraram **enums nativos do PostgreSQL**. Eles causaram problemas três vezes:

- o autogenerate do Alembic tenta recriar um enum que já existe (`type already exists`);
- acrescentar um valor exige `ALTER TYPE ... ADD VALUE`, que não roda dentro de transação e não sai no `downgrade`;
- o SQLAlchemy grava o **nome** do membro (`LOAN`), não o valor (`loan`), e o `create_all` dos testes não pega a diferença.

## Opções consideradas

1. **Continuar com enum nativo** para conjuntos novos.
2. **Coluna de texto com `CHECK`** listando os valores válidos.

## Decisão

Escolhida: **texto com `CHECK`** para todo conjunto novo de valores (por exemplo, `categories.dre_group` e `categories.ir_kind`). Os enums que já existem continuam, e acrescentar valor neles segue a receita de R-11.1.

## Consequências

- **Positivas:** acrescentar um valor é uma migração comum, transacional e reversível.
- **Negativas:** dois padrões convivem no banco. Ao mexer num enum antigo: usar `postgresql.ENUM(..., create_type=False)`, rodar `ADD VALUE` em bloco autocommit e cobrir com `tests/test_migrations.py`, que aplica todas as migrações num banco vazio e grava uma conta de cada tipo.

## Mais informações

- [Modelo de dados — enums](../arquitetura/modelo-de-dados.md#enums-e-valores-fixos).
