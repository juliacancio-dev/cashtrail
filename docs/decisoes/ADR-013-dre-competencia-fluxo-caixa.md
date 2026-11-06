# ADR-013 — DRE por competência e fluxo por caixa, numa slice só de leitura

- **Status:** Aceita
- **Data:** 2026-10-09
- **Contexto de origem:** Marco 10 ([doc 25, decisões 1, 2, 3 e 8](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md))

## Contexto e problema

O Marco 10 trouxe dois relatórios que parecem iguais e respondem perguntas diferentes: "quanto gastei em março?" (DRE) e "vai faltar dinheiro em março?" (fluxo de caixa). A compra no cartão é o caso que separa os dois.

## Opções consideradas

- **Regime:** um relatório só, ou **DRE por competência** (data da compra) e **fluxo por caixa** (data em que o dinheiro se move).
- **Estrutura do DRE:** lista simples por categoria; **grupo de DRE em cada categoria**; ou categorias hierárquicas.
- **Onde calcular:** em cada slice dona do dado, ou numa **slice nova só de leitura**.

## Decisão

- DRE por **competência** e fluxo por **caixa**: a compra no cartão entra no DRE na data da compra e no fluxo no vencimento da fatura.
- Um campo `dre_group` por categoria (seis grupos), como o "grupo do DRE" dos ERPs; categoria sem grupo cai em "Sem grupo".
- Saldo inicial por conta (`opening_balance`), sem o qual não existe projeção de saldo.
- Cálculo na slice **`reports`**, que não tem tabela própria e da qual ninguém depende (exceto `tax`, que lê o patrimônio).

## Consequências

- **Positivas:** as duas visões ficam consistentes e explicáveis; os relatórios não acoplam as slices de escrita entre si.
- **Negativas:** `reports` lê de muitas slices pelos services públicos; uma regra nova de dinheiro precisa ser refletida ali.

## Mais informações

- [DRE e fluxo de caixa](../produto/regras-de-negocio.md#4-dre-e-fluxo-de-caixa).
