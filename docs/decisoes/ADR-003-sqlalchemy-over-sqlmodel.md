# ADR-003 — SQLAlchemy 2.0 em vez de SQLModel

- **Status:** Aceita
- **Data:** 2026-09-16

## Contexto e problema

O backend em FastAPI precisava de um ORM e de uma ferramenta de migração.

## Opções consideradas

1. **SQLAlchemy 2.0 + Alembic**, com schemas Pydantic separados dos modelos ORM.
2. **SQLModel**, do mesmo autor do FastAPI, que une modelo ORM e schema Pydantic numa classe só.

## Decisão

Escolhida: **SQLAlchemy 2.0 + Alembic**, porque mantém o modelo de persistência separado do contrato da API (o modelo ORM nunca é exposto direto) e é a habilidade mais madura e mais pedida no mercado Python.

## Consequências

- **Positivas:** separação clara entre persistência (`models.py`) e contrato (`schemas.py`); documentação e ecossistema maduros.
- **Negativas:** mais código repetido, porque cada entidade tem modelo e schema.

## Mais informações

- [Anatomia de uma slice](../../backend/README.md#anatomia-de-uma-slice).
