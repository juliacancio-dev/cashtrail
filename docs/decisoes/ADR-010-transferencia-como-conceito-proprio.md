# ADR-010 — Transferência como conceito próprio, neutra no resultado

- **Status:** Aceita
- **Data:** 2026-10-09
- **Contexto de origem:** Marco 9 ([doc 24, decisão 1](../marcos/24-marco-9-cartoes-e-faturas.md))

## Contexto e problema

Pagar a fatura do cartão move dinheiro da conta corrente para o cartão. Se esse pagamento virasse despesa, a compra no cartão (já registrada como despesa) seria contada duas vezes. Até o Marco 8 o sistema só conhecia receita e despesa.

## Opções consideradas

1. **Transferência como conceito próprio**, numa slice `transfers` com tabela própria.
2. **Novo valor `transfer` em `TransactionType`**, dentro da tabela de lançamentos.
3. **Pagamento como despesa**, ignorando as compras do cartão nos totais (regime de caixa).

## Decisão

Escolhida: **transferência como conceito próprio**. Ela não toca a tabela de lançamentos nem nenhum total existente. A opção 2 obrigaria filtrar transferências em dashboard, orçamentos, metas e importação; a opção 3 jogaria o gasto para o mês errado.

## Consequências

- **Positivas:** a mesma primitiva serviu depois para pagar parcela de dívida (principal), receber empréstimo e comprar investimento, todos neutros no resultado (RB-014).
- **Negativas:** o saldo de uma conta passa a somar duas fontes (lançamentos e transferências), e todo relatório precisa considerar as duas.

## Mais informações

- [Contagem única](../produto/regras-de-negocio.md#1-contagem-única) e [ADR-012](ADR-012-contas-nao-caixa.md).
