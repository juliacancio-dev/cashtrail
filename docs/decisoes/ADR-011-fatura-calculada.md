# ADR-011 — Fatura do cartão calculada a partir das compras

- **Status:** Aceita
- **Data:** 2026-10-09

## Contexto e problema

A fatura podia ser um dado gravado (uma conta a pagar criada no fechamento) ou uma visão calculada a partir das compras do ciclo.

## Opções consideradas

1. **Fatura calculada** a partir das compras ligadas ao ciclo: fonte única da verdade.
2. **Fatura gravada** como conta a pagar do Marco 8, criada no fechamento.

## Decisão

Escolhida: **fatura calculada**. Gravar duplicaria o total (na compra e no compromisso), ficaria desatualizado quando uma compra fosse lançada depois do fechamento e exigiria uma exceção na baixa, que no Marco 8 sempre cria despesa.

## Consequências

- **Positivas:** a fatura nunca diverge das compras; mover uma compra de fatura é só mudar o vínculo.
- **Negativas:** a fatura não aparece na lista de "A pagar e a receber"; ela fica em Cartões, com alerta no dashboard, e o fluxo de caixa consome contas a pagar **e** faturas.

## Mais informações

- [Cartões e faturas](../produto/regras-de-negocio.md#2-cartão-de-crédito).
