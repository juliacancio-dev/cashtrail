# ADR-007 — Vertical slices com `transactions` como núcleo

- **Status:** Aceita
- **Data:** 2026-09-16

## Contexto e problema

O backend começaria com 9 funcionalidades e cresceria (hoje são 19 slices). Era preciso escolher como organizar o código.

## Opções consideradas

1. **Camadas horizontais:** `controllers/`, `services/` e `repositories/` globais.
2. **Vertical slices:** uma pasta por funcionalidade, com rota, schema, regra, persistência e testes juntos.

## Decisão

Escolhida: **vertical slices**, com `features/transactions` como núcleo do domínio. As demais slices podem depender dela; ela não depende de nenhuma. Uma slice só usa outra pela camada pública `service.py`, nunca pelo `repository.py` ou pelos modelos ORM.

## Consequências

- **Positivas:** uma mudança fica quase sempre contida numa pasta; dá para testar cada funcionalidade isoladamente.
- **Negativas:** funções pequenas às vezes são duplicadas de propósito (por exemplo, `split_amount` em `commitments` e `credit_cards`) para não criar dependência entre slices só por cinco linhas.
- **Regra transversal:** a única infraestrutura compartilhada é `core/` no backend e `lib/` no frontend, cada uma com responsabilidades nomeadas; não existem pastas genéricas como `utils/` ou `shared/`.

## Mais informações

- [Arquitetura](../arquitetura/visao-geral.md#vertical-slices) e [regras de dependência](../../backend/README.md#regras-de-dependência).
