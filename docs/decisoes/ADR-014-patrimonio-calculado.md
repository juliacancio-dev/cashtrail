# ADR-014 — Patrimônio histórico calculado na hora, sem snapshots

- **Status:** Aceita
- **Data:** 2026-10-15
- **Contexto de origem:** Marco 12 ([doc 27, decisões 1 e 3](../marcos/27-marco-12-patrimonio-e-balanco.md))

## Contexto e problema

A evolução do patrimônio mostra o patrimônio líquido no fim de cada mês. Ele pode ser recalculado do histórico a cada pedido ou gravado por um job.

## Opções consideradas

1. **Calcular na hora**, a partir dos saldos por data, das avaliações dos bens e das dívidas na data.
2. **Snapshots mensais** gravados por um job.

## Decisão

Escolhida: **calcular na hora**, porque o histórico é a fonte da verdade e um snapshot fica errado quando o usuário corrige um lançamento antigo. Pelo mesmo motivo, o valor dos bens é guardado como **histórico de avaliações por data** (`asset_valuations`), não como um "valor atual".

## Consequências

- **Positivas:** sempre consistente, sem job nem invalidação de dado derivado.
- **Negativas:** cada abertura recalcula 12 meses. Para uso pessoal é rápido; **medir** se o histórico crescer muito. A saída prevista é um único passe pelo histórico em vez de uma consulta por mês.

## Mais informações

- [Patrimônio](../produto/regras-de-negocio.md#7-patrimônio).
