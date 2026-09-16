# ADR-003 — SQLAlchemy 2.0 (não SQLModel)

**Status**: Aceito

**Contexto**: escolha do ORM para o backend FastAPI.

**Alternativas**: SQLAlchemy 2.0 (ORM maduro e mais adotado do mercado Python) vs. SQLModel (une modelo ORM e schema Pydantic na mesma classe, do mesmo autor do FastAPI).

**Decisão**: SQLAlchemy 2.0 + Alembic, com schemas Pydantic escritos separadamente do modelo ORM.

**Justificativa**: mantém a separação de camadas (nunca expor o modelo ORM direto na API); é a habilidade mais transferível e reconhecida no mercado de trabalho, comparado a SQLModel, que é mais recente e menos exigido em vagas.

**Consequências**: mais código de "boilerplate" (schema + modelo separados), mas separação de responsabilidades mais limpa entre persistência e contrato de API.
