# ADR-009 — Partida simples, sem partidas dobradas

- **Status:** Aceita
- **Data:** 2026-10-06

## Contexto e problema

O produto passou de "controle de gastos" para um ERP pessoal: contas a pagar, cartões, DRE, dívidas, patrimônio e investimentos. Sistemas contábeis de verdade usam partidas dobradas (todo lançamento tem débito e crédito).

## Opções consideradas

1. **Partida simples:** cada lançamento é uma entrada ou uma saída, como no MVP; DRE, fluxo e balanço são visões derivadas.
2. **Partidas dobradas:** todo lançamento tem débito e crédito em contas contábeis.

## Decisão

Escolhida: **partida simples**, porque os ERPs pesquisados entregam fluxo de caixa, DRE e balanço sem exigir que o usuário entenda débito e crédito, e o ganho de rigor para uso pessoal não paga a complexidade de mudar todos os lançamentos e a tela de lançamento.

## Consequências

- **Positivas:** o modelo do MVP continua válido; a tela de lançamento continua simples.
- **Negativas:** a consistência entre visões depende de regras explícitas, como "transferência não é receita nem despesa" ([ADR-010](ADR-010-transferencia-como-conceito-proprio.md)) e "conta que não é caixa" ([ADR-012](ADR-012-contas-nao-caixa.md)), testadas com testes de propriedade.
- **Revisar se:** surgir uma necessidade concreta que só partidas dobradas resolvem (por exemplo, balancete auditável).

## Mais informações

- [Regras de negócio](../produto/regras-de-negocio.md).
