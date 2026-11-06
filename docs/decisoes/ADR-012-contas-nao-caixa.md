# ADR-012 — Cartão, dívida e investimento como tipos de conta

- **Status:** Aceita
- **Data:** 2026-10-09 (dívidas), estendida em 2026-10-15 (investimentos)

## Contexto e problema

Dívidas e investimentos precisavam de saldo, de transferências e de entrar no patrimônio. O cartão (Marco 9) já era uma conta do tipo `credit_card` com uma tabela de configuração.

## Opções consideradas

1. **Conta de um tipo novo** (`loan`, `investment`) + tabela com a configuração, como o cartão.
2. **Entidade própria** (`debts`, `investments`) sem conta, com saldo calculado nela.
3. **Sem entidade:** parcelar contas a pagar (dívida) ou cadastrar como bem (investimento).

## Decisão

Escolhida: **conta de um tipo novo + configuração**. Reaproveita transferência, saldo e relatórios, e o patrimônio sai de graça. A opção 2 duplicaria a lógica de saldo; a opção 3 erraria o DRE (principal viraria despesa) ou perderia quantidade e preço médio.

## Consequências

- **Positivas:** uma única fórmula de saldo para todas as contas; o saldo da conta `loan` é o saldo devedor, o da conta `investment` é o custo remanescente.
- **Negativas:** "conta de caixa" deixou de ser "conta que não é cartão". Existe um único predicado, `NON_CASH_TYPES` em `accounts/models.py`, usado por saldos, fluxo de caixa e dashboard; código novo precisa usá-lo.
- **Negativas:** cada tipo novo exigiu `ALTER TYPE ... ADD VALUE` no enum nativo (risco R-11.1), o que motivou o [ADR-019](ADR-019-texto-com-check-em-vez-de-enum.md).
- **Regra derivada:** o patrimônio usa o **valor de mercado** dos investimentos e deixa o saldo da conta `investment` (custo) de fora, para não contar duas vezes (RB-032).

## Mais informações

- [Tipos de conta](../produto/regras-de-negocio.md#tipos-de-conta).
