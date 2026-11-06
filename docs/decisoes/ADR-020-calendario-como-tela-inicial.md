# ADR-020 — Calendário do dinheiro como tela inicial, calculado no backend

- **Status:** Aceita
- **Data:** 2026-10-26

## Contexto e problema

O redesign trocou a interface padrão do shadcn por uma identidade própria. O conceito aprovado (após cinco rodadas de protótipo) põe um **calendário do dinheiro** na entrada: saldo de hoje, o dia mais apertado do mês, uma linha de saldo e o detalhe de cada dia.

## Opções consideradas

- **Tela inicial:** o calendário substitui o dashboard; o calendário como tela a mais; ou os dois fundidos.
- **Cálculo:** uma rota nova que agrega por dia no backend, ou o frontend somando os itens do fluxo de caixa.

## Decisão

- O calendário (`/calendar`) é a tela inicial. O dashboard continua existindo como **Resumo do mês**.
- O cálculo fica no backend, em `GET /reports/calendar?month=AAAA-MM`, reaproveitando o fluxo de caixa (sem tabela nova). Conta de dinheiro fica onde há testes de propriedade, não no navegador.
- A previsão só conhece o que está agendado; o detalhe de um dia de previsão avisa isso numa frase curta.

## Consequências

- **Positivas:** o saldo de hoje do calendário bate com `/reports/balances`, e o fechamento do mês bate com o fluxo de caixa (testado).
- **Negativas:** gastos do dia a dia ainda não lançados não entram na previsão, então o futuro parece mais folgado. Melhorar a previsão é item de backlog.

## Mais informações

- [Calendário](../produto/regras-de-negocio.md#5-calendário-do-dinheiro).
