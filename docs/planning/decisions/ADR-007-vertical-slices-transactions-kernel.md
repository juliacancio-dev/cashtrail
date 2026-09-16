# ADR-007 — Vertical Slice Architecture com `transactions` como núcleo compartilhado

**Status**: Aceito

**Contexto**: como organizar o código do backend entre as 9 funcionalidades do sistema.

**Alternativas**: arquitetura em camadas horizontais (controllers/services/repositories globais) vs. Vertical Slice Architecture (uma pasta por funcionalidade).

**Decisão**: Vertical Slice Architecture, com `features/transactions` como a única slice da qual as demais (`budgets`, `goals`, `dashboard`, `recurring`, `statement_import`) legitimamente dependem — nunca o contrário.

**Justificativa**: `transactions` é o dado central do domínio, não uma decisão arbitrária de acoplamento; outras slices chamam sua camada `service` pública, nunca seu `repository`/`models` diretamente.

**Consequências**: mudança numa funcionalidade fica majoritariamente contida na própria pasta; a única infraestrutura verdadeiramente transversal (`core/` no backend, `lib/` no frontend) tem responsabilidade nomeada e limitada, evitando pastas genéricas tipo `utils/`/`shared/`.
