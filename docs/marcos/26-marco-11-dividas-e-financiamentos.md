# CashTrail — Marco 11: Dívidas e financiamentos (desenho)

> Quarto marco da fase "ERP pessoal" ([22](22-erp-pessoal-discovery.md)); usa o Marco 8 ([23](23-marco-8-contas-a-pagar-receber.md)), as transferências do Marco 9 ([24](24-marco-9-cartoes-e-faturas.md)) e o saldo inicial do Marco 10 ([25](25-marco-10-fluxo-de-caixa-e-dre.md)). Segue o fluxo do projeto: **desenho e decisões antes de qualquer código**. Nada aqui foi implementado.

Legenda: **FATO** (código verificado) · **INFERÊNCIA** (conclusão minha) · **HIPÓTESE** · **DESCONHECIDO**.

## 1. Objetivo e critério de saída

**Objetivo:** cadastrar um empréstimo ou financiamento, ver o **cronograma de parcelas**, pagar cada parcela e saber o **saldo devedor** a qualquer momento, com o resultado (DRE) mostrando só o que é custo de verdade: os **juros e encargos**, não o valor tomado emprestado nem a devolução do principal.

**Critério de saída:**
1. Um empréstimo de R$ 10.000 em 10x entra como dívida de R$ 10.000; **não** aparece como receita ao ser recebido.
2. Pagar a parcela 1 reduz o saldo devedor **só pela parte do principal**; os juros aparecem como despesa financeira no DRE.
3. As 10 parcelas aparecem em "A pagar/receber", no dashboard e no fluxo de caixa futuro.
4. Saldo devedor = principal contratado − principal já amortizado, e bate com a conta manual do cronograma.

## 2. O problema central: tomar e pagar dívida não é receita nem despesa

**INFERÊNCIA (contabilidade básica, a mesma lógica de RB-014 do cartão):**
- Receber R$ 10.000 do banco aumenta o dinheiro **e** a dívida; o patrimônio não muda. **Não é receita.**
- Pagar uma parcela de R$ 1.100 (R$ 1.000 de principal + R$ 100 de juros) reduz a dívida em R$ 1.000 e gasta R$ 100. **Só os R$ 100 são despesa.**

**FATO — o código hoje:**
- `Commitment` aceita parcelas (`installment_group_id`) e a baixa gera **uma despesa do valor inteiro** na categoria do compromisso. Se o usuário usar só isso, o DRE conta o principal como despesa e o empréstimo recebido como receita: **resultado errado**.
- `TransactionType` só tem `income`/`expense`; transferência já existe (Marco 9) e é neutra para DRE/dashboard.
- `accounts.type` é um **enum nativo do Postgres** (`account_type`: checking, savings, credit_card). Adicionar valor exige `ALTER TYPE ... ADD VALUE` (ver risco R-11.1).

## 3. Como os apps resolvem (pesquisa)

**DESCONHECIDO / NÃO PESQUISADO NA FONTE:** não verifiquei a documentação de Mobills, Organizze ou Minhas Economias para dívidas. O que segue é o desenho contábil padrão, que é independente do app:

- **FATO (matemática financeira padrão):** *Tabela Price* = parcelas iguais, PMT = P·i / (1 − (1+i)^−n), juros caem e principal sobe a cada parcela. *SAC* = amortização constante P/n, juros sobre o saldo, parcelas decrescentes. Sem juros (i = 0) = n parcelas iguais de P/n.
- **FATO (comportamento real de bancos):** o valor da parcela do contrato costuma incluir IOF, seguro e tarifas; o CET real difere da taxa nominal. Por isso a parcela do contrato **pode não bater** com a calculada.
- **HIPÓTESE:** para uso pessoal, ninguém quer recalcular o contrato; quer **informar o que o banco mandou** e acompanhar o saldo. A calculadora serve para conferir e para simular.

## 4. Escopo proposto

**Dentro:**
- Cadastro da dívida: nome, credor, principal, data da contratação, nº de parcelas, 1º vencimento, sistema (Price / SAC / sem juros / informado), taxa mensal, conta que recebeu o dinheiro (opcional), conta padrão de pagamento, categoria dos encargos.
- Geração do cronograma, com edição do valor de cada parcela.
- Parcelas como contas a pagar (Marco 8) → aparecem em dashboard, alertas e fluxo de caixa sem código novo nessas telas.
- Pagar parcela separando principal × encargos; desfazer.
- Saldo devedor, total já pago, total de juros pagos e projetado, próxima parcela.
- Quitação antecipada (paga o saldo devedor e cancela as parcelas restantes).
- **Amortização extraordinária com recálculo** (decisão 4 da Julia): paga um valor extra de principal e o cronograma restante é recalculado, **reduzindo o prazo** (mantém a parcela) **ou reduzindo a parcela** (mantém o prazo), à escolha na hora.
- Resumo de dívidas no dashboard (saldo devedor total).

**Fora (marcos seguintes ou depois):**
- Portabilidade e renegociação de dívida.
- Empréstimo **concedido** a terceiros (a receber com juros).
- Cálculo de CET/IOF, taxa variável (TR, CDI, IPCA) e correção monetária.
- Bem financiado como ativo (carro/imóvel): é Marco 12 (patrimônio).
- Cartão e rotativo: seguem no Marco 9.

## 5. Requisitos propostos

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RF-032 | Cadastrar dívida (principal, parcelas, 1º vencimento, sistema, taxa) | Valida principal > 0, parcelas 1–360, taxa ≥ 0; só categorias/contas do próprio usuário |
| RF-033 | Gerar cronograma (Price, SAC, sem juros ou informado) | Σ principal das parcelas = principal da dívida (a última absorve o arredondamento) |
| RF-034 | Editar valor/vencimento de parcela em aberto | Alterar valor muda só os encargos da parcela; o principal do cronograma não muda |
| RF-035 | Receber o dinheiro da dívida (opcional) | Cria transferência da conta da dívida para a conta corrente; **não** é receita |
| RF-036 | Pagar parcela separando principal e encargos; desfazer | Principal vira transferência para a conta da dívida; encargos viram despesa financeira |
| RF-037 | Saldo devedor e resumo da dívida | Saldo = principal − principal amortizado; mostra pago, juros pagos, próxima parcela |
| RF-038 | Quitação antecipada | Paga o saldo devedor e cancela parcelas abertas; sem recalcular juros (valor informado pelo usuário) |
| RF-039 | Saldo devedor total no dashboard e no fluxo | Somado ao cartão como "dívida total" |
| RF-040 | Amortização extraordinária com recálculo (reduzir prazo ou reduzir parcela) | O valor extra reduz o saldo devedor; as parcelas abertas são regeradas pelo mesmo sistema e taxa; Σ principal restante = novo saldo devedor; parcelas já pagas não mudam |

| ID | Regra de negócio |
|---|---|
| RB-023 | Receber o valor da dívida e amortizar o principal **não** são receita nem despesa (mesma lógica de RB-014) |
| RB-024 | Encargos (parcela − principal da parcela) são despesa com grupo de DRE `financial_expense` por padrão |
| RB-025 | Parcela paga não pode ter o valor editado; só desfazendo a baixa |
| RB-027 | Recálculo só altera parcelas **em aberto**; as parcelas editadas à mão (RF-034) voltam ao valor calculado, com aviso antes de confirmar |
| RB-026 | Saldo devedor nunca fica negativo; pagamento de parcela maior que o saldo restante é rejeitado |

## 6. Decisões

### DECISÃO 1 — Como representar a dívida

- **ALTERNATIVAS:**
  - **(a)** Dívida = **conta** do tipo `loan` + tabela `debts` com a configuração (igual ao cartão). Saldo devedor = saldo negativo da conta.
  - **(b)** Dívida = entidade própria `debts` + `debt_installments`, sem conta; saldo devedor calculado só nela.
  - **(c)** Só parcelar contas a pagar (`Commitment` com parcelas), sem entidade de dívida.
- **EVIDÊNCIAS:** o cartão (Marco 9) já usa (a): conta `credit_card` + configuração, e a dívida entra no patrimônio pelo saldo da conta. Transferências já existem e já são neutras no DRE. `opening_balance` negativo já representa dívida inicial (Marco 10). O Marco 12 vai somar saldos de contas.
- **TRADE-OFFS:**
  - (a) reaproveita transferência, saldo e relatórios, e o patrimônio sai de graça; **custo:** novo valor no enum `account_type` (migração delicada, R-11.1) e todo lugar que trata "conta de caixa" precisa excluir `loan` (hoje exclui só `credit_card`).
  - (b) evita o enum, mas **duplica** a lógica de saldo e de transferência e deixa o patrimônio dependente de mais um caminho de cálculo.
  - (c) é o menor esforço e **erra o DRE** (principal vira despesa).
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Média-alta; o ponto de risco é só a migração do enum, que dá para testar com o mesmo ciclo up/down/up usado antes.

### DECISÃO 2 — Como o cronograma é gerado

- **ALTERNATIVAS:** **(a)** calculadora Price/SAC/sem juros com valor de cada parcela editável; **(b)** só valores informados parcela a parcela.
- **EVIDÊNCIAS:** parcelas reais incluem IOF/seguro/tarifas (seção 3), então a calculada raramente bate com a do contrato; mas digitar 48 parcelas à mão é ruim.
- **TRADE-OFFS:** (a) dá o split principal × juros sem esforço e deixa corrigir o valor final; **custo:** mais código e mais testes de arredondamento. (b) é simples, mas **sem taxa não há como separar principal de juros**, e o DRE fica impreciso.
- **RECOMENDAÇÃO:** **(a)**. Na parcela editada, o **principal continua o do cronograma** e a diferença vira encargo (RF-034). **CONFIANÇA:** Alta.

### DECISÃO 3 — Como a baixa da parcela afeta o resultado

- **ALTERNATIVAS:** **(a)** a baixa gera duas coisas: transferência do principal para a conta da dívida + despesa de encargos na categoria de juros; **(b)** a baixa gera uma despesa do valor total (como hoje) e o DRE trata principal como despesa.
- **EVIDÊNCIAS:** seção 2; é a regra contábil padrão e o mesmo desenho do pagamento de fatura.
- **TRADE-OFFS:** (a) deixa DRE e patrimônio corretos; **custo:** a baixa de parcela de dívida **não pode** usar o caminho comum de `settle_commitment` (que cria uma despesa só). Preciso estender o serviço de compromissos ou orquestrar a baixa na slice `debts` (**INFERÊNCIA:** a primeira tentativa é a orquestração em `debts`, chamando os services públicos de `transactions`/`transfers`/`commitments`, sem tocar em repository de outra slice; valido isso no início da implementação).
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Alta para a regra; média para o ponto de integração com `commitments`.

### DECISÃO 4 — Escopo de v1

- **ALTERNATIVAS:** **(a)** v1 enxuto: cronograma, baixa, saldo, quitação simples; amortização com recálculo e empréstimo concedido depois; **(b)** incluir amortização parcial com recálculo.
- **TRADE-OFFS:** recalcular cronograma depois de amortização extra é a parte com mais regra (prazo × parcela, reduzir prazo ou valor) e o menos usado por quem só quer acompanhar o saldo. Entra no backlog sem bloquear o patrimônio (Marco 12), que só precisa do saldo devedor.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Alta.

## 7. Modelo de dados proposto

- `accounts.type` ganha o valor `loan`.
- `debts` (1 por conta `loan`): `account_id` unique, `creditor`, `principal`, `contracted_at`, `installments`, `system` (String + CHECK: `price|sac|zero|manual`, **não** enum nativo), `monthly_rate` Numeric(7,4), `first_due_date`, `payment_account_id`, `interest_category_id`, `status` (`active|paid_off|canceled`).
- `debt_installments`: `debt_id`, `number`, `commitment_id` unique, `principal_part`, `scheduled_amount`. A parcela em si é um `Commitment` (payable, `installment_group_id` = id da dívida) → alertas, dashboard e fluxo de caixa funcionam sem mudança.
- Saldo devedor = `principal` − Σ `principal_part` das parcelas pagas (+ pagamentos de quitação).

**Dependências de slice:** `debts` → `transactions`, `transfers`, `commitments`, `accounts`, `categories` (todas pelo `service` público). Ninguém depende de `debts`, exceto `reports` (saldo devedor) e `dashboard` (resumo) em leitura.

## 8. Plano de implementação (etapas)

1. Migração: valor `loan` no enum + tabelas `debts`/`debt_installments` (ciclo up/down/up/check).
2. Calculadora de cronograma (Price/SAC/sem juros) com testes de propriedade: Σ principal = P, saldo nunca negativo, última parcela fecha.
3. Criar dívida + gerar parcelas como compromissos; receber o dinheiro (transferência).
4. Baixa de parcela separando principal × encargos; desfazer; quitação.
4b. Amortização extraordinária: gerar o cronograma restante a partir do saldo devedor (reduzir prazo ou parcela), com pré-visualização antes de confirmar.
5. Saldo devedor, resumo, integração em `reports` (saldo de caixa **exclui** `loan`; DRE já exclui transferências) e no dashboard.
6. Frontend: lista de dívidas, nova dívida com simulação do cronograma, detalhe com parcelas e botão de pagar, saldo no dashboard.
7. Verificação no navegador e documentação.

## 9. Riscos

| ID | Risco | Mitigação |
|---|---|---|
| R-11.1 | `ALTER TYPE ... ADD VALUE` em migração Alembic (o projeto já teve problema com enums nativos duas vezes) | Usar `autocommit_block`, não usar o valor novo na mesma transação, testar up/down/up e `alembic check`; o `downgrade` não remove o valor do enum (documentado) |
| R-11.2 | Cronograma calculado diverge do contrato (IOF, seguro, carência) | Valor da parcela editável; diferença vira encargo; aviso na tela |
| R-11.3 | Lugares que tratam "conta de caixa" como `!= credit_card` passam a incluir `loan` | Centralizar a regra num único predicado e cobrir com teste de saldo de caixa (`reports/balances_dre.py`, `cash_flow.py`, `credit_cards`) |
| R-11.5 | Recálculo após amortização diverge do que o banco faz (carência, IOF, data-base) | Pré-visualização obrigatória, parcelas recalculadas editáveis, aviso de que o contrato manda; confronto com caso real quando houver |
| R-11.4 | Arredondamento acumulado em 360 parcelas | Última parcela absorve a diferença; teste de propriedade |

## 10. Perguntas para a Julia

1. **Decisão 1:** dívida como **conta do tipo `loan`** (recomendado) ou entidade separada?
2. **Decisão 2:** calculadora Price/SAC com valor editável (recomendado) ou só parcelas informadas?
3. **Decisão 3:** baixa separando principal e juros (recomendado)?
4. **Decisão 4:** v1 enxuto, sem amortização com recálculo (recomendado)?
5. Você tem hoje alguma dívida real para validar (financiamento, empréstimo, parcelamento com juros)? Com **taxa, nº de parcelas e valor da parcela** eu confiro a calculadora contra o contrato.

**STATUS:** decisões 1, 2 e 3 aprovadas como recomendadas (conta `loan`, calculadora editável, baixa separando principal e encargos). **Decisão 4: a Julia escolheu incluir a amortização com recálculo na v1** (diferente da recomendação; escopo maior, ver RF-040/RB-027/R-11.5). **Padrão da amortização extra: reduzir o prazo** (mantém a parcela); reduzir a parcela fica como opção. Sem dívida real para validar agora: a calculadora é validada por testes de propriedade e exemplos de manual (Price e SAC). Nenhum código escrito.

**IMPLEMENTADO (2026-10-09):** backend (553 testes, incluindo cronograma, API e migração real) e frontend (`/debts`, saldo devedor no dashboard, tipo `loan` em `/accounts`) prontos e verificados no navegador (empréstimo de 1.000 a 2% em 12x: parcela 94,56; DRE do mês só com R$ 20 de juros; extra de R$ 400 reduz o prazo para 6 parcelas e o saldo devedor para R$ 525,44).

**Decisões ao codar:**
- `Commitment.debt_id` e `CommitmentSettlement.transfer_id` (com `transaction_id` agora opcional): a baixa de parcela de dívida cria só a despesa dos encargos e a transferência do principal; pagar/editar/cancelar parcela pelas rotas genéricas de `/commitments` devolve 409 (use `/debts`).
- Sem `received_account_id`, a conta da dívida nasce com saldo inicial −principal (dívida já existente); com ele, o dinheiro entra por transferência.
- Parcelas de dívida são pagas inteiras (sem baixa parcial).
- Pagamento extra **não tem desfazer** na v1 (regera o cronograma); quitação paga o saldo devedor de principal, sem desconto de juros futuros.
- Valor do enum nativo é `LOAN` (SQLAlchemy grava o NOME do membro, não o valor); um teste de migração real (`tests/test_migrations.py`) cobre isso, pois `create_all` não pegaria.
