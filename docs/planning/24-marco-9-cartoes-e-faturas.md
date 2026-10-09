# CashTrail — Marco 9: Cartões de crédito e faturas (desenho)

> Segundo marco da fase "ERP pessoal" ([22](22-erp-pessoal-discovery.md)), depende do Marco 8 ([23](23-marco-8-contas-a-pagar-receber.md)). Segue o fluxo do projeto: **desenho e decisões antes de qualquer código**. Nada aqui foi implementado.

Legenda: **FATO** (fonte ou código verificado) · **INFERÊNCIA** (conclusão minha) · **HIPÓTESE** · **DESCONHECIDO**.

## 1. Objetivo e critério de saída

**Objetivo:** registrar compras no cartão (inclusive parceladas), ver a **fatura de cada ciclo**, pagar a fatura (total ou parcial) e saber o **limite usado e disponível**, sem contar o gasto duas vezes.

**Critério de saída:** (1) uma compra de R$ 100 no cartão entra na fatura certa e no dashboard **uma vez só**, e pagar a fatura **não** a conta de novo; (2) uma compra em 3x aparece nas 3 faturas seguintes; (3) o total de cada fatura bate com a soma manual das compras do ciclo; (4) o limite disponível bate com limite menos o que ainda se deve.

## 2. O problema central: não contar duas vezes

Hoje uma compra no cartão é um lançamento de despesa numa conta do tipo `credit_card`, e o dashboard soma todas as despesas. Se o usuário **também** lançar "pagamento da fatura" como despesa na conta corrente, o gasto aparece **duas vezes**.

**INFERÊNCIA (contabilidade básica):** pagar a fatura não é um gasto novo; é quitar uma dívida que já foi reconhecida na compra. É uma **transferência** da conta corrente para o cartão: sai de uma conta, entra na outra, e o resultado do período não muda.

**FATO — o código:** `TransactionType` só tem `income` e `expense`; **não existe transferência** nem **saldo por conta** (busca por "balance/saldo" na slice `accounts` não encontra nada). Então o Marco 9 precisa criar o conceito de transferência. E ele serve de base também para o patrimônio (Marco 12) e para aportes em investimentos (Marco 13).

## 3. Como os apps resolvem (pesquisa)

**FATO — Mobills** ([cartão manual](https://mobills.zendesk.com/hc/en-us/articles/360052676093-How-to-create-a-credit-card-expense), [parcelado](https://mobills.zendesk.com/hc/pt-br/articles/44243003508123-Como-criar-uma-transa%C3%A7%C3%A3o-parcelada-no-cart%C3%A3o-de-cr%C3%A9dito-manual), [pagar fatura](https://mobills.zendesk.com/hc/en-us/articles/360052894033-How-to-pay-a-credit-card-statement)):
- Ao cadastrar o cartão informa-se **limite, bandeira, conta de pagamento, datas de fechamento e vencimento**.
- Compra no cartão é um tipo próprio, **"despesa de cartão de crédito"**, diferente de despesa debitada na conta.
- Ao lançar, o usuário **escolhe a fatura** à qual a compra pertence.
- **Parcelas** aparecem na fatura de cada mês, identificadas como 1/10, 2/10...
- Pagamento da fatura: **total, parcial ou adiantado**. No parcial, o app fecha a fatura e cria uma despesa do valor restante na fatura seguinte.
- **NÃO ENCONTRADO:** a regra exata de como o pagamento total é classificado (transferência ou despesa); a inferência da seção 2 é minha.
- **NÃO ENCONTRADO:** a documentação do Organizze (nenhuma fonte específica).

**FATO — regra de fechamento** ([Mobills](https://www.mobills.com.br/blog/cartao-de-credito/melhor-dia-de-compra-cartao-de-credito/), [Mercado Pago](https://www.mercadopago.com.br/blog/data-de-vencimento-fechamento-fatura-do-cartao), [C6](https://www.c6bank.com.br/blog/fechamento-e-vencimento-da-fatura)): a compra entra na **primeira fatura que fechar depois dela**; o vencimento vem alguns dias após o fechamento (em geral 7 a 10). **A compra feita no próprio dia do fechamento é ambígua**: depende do horário e do processamento do banco. Por isso a data de uma compra pode cair em fatura diferente da esperada, e o usuário precisa poder corrigir.

## 4. Escopo

**Dentro:** transferência entre contas; cadastro do cartão (fechamento, vencimento, limite); compra no cartão com escolha de fatura; compra parcelada; fatura por ciclo; pagamento total/parcial da fatura (como transferência) e desfazer; limite usado/disponível; alerta de faturas no dashboard.

**Fora (marcos seguintes):** juros e rotativo calculados automaticamente (o usuário lança os juros como despesa), pagamento adiantado com crédito na fatura seguinte, antecipação de parcelas, importação de fatura em PDF, Open Finance, saldo por conta e saldo inicial (Marco 12).

## 5. Requisitos propostos

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RF-023 | Transferência entre contas (criar, listar, desfazer) | Move valor de uma conta para outra e **não** altera receitas, despesas, orçamentos nem DRE |
| RF-024 | Cadastro de cartão: conta do tipo cartão, dia de fechamento, dia de vencimento, limite opcional, conta padrão de pagamento | Cartão criado só para conta `credit_card` do próprio usuário, uma configuração por conta |
| RF-025 | Compra no cartão, com a fatura escolhida (padrão: calculada pela data) | A compra cria **uma** despesa na conta do cartão e fica ligada a uma fatura |
| RF-026 | Compra parcelada no cartão | R$ 300 em 3x cria 3 despesas de R$ 100, uma em cada fatura consecutiva, "(1/3)" a "(3/3)" |
| RF-027 | Faturas por ciclo: período, vencimento, total, pago, saldo, situação | Total = soma das compras do ciclo menos estornos |
| RF-028 | Pagar fatura (total ou parcial) e desfazer o pagamento | Cria uma transferência da conta de pagamento para o cartão; desfazer apaga o vínculo e a transferência |
| RF-029 | Limite usado e disponível | Usado = dívida total do cartão, inclusive parcelas futuras |
| RF-030 | Alerta de faturas vencidas e a vencer no dashboard | Aparece junto do alerta de contas a pagar do Marco 8 |

| ID | Regra de negócio |
|---|---|
| RB-014 | Transferência **não é** receita nem despesa: fica fora de dashboard, orçamentos, metas e DRE |
| RB-015 | Origem e destino de uma transferência são contas diferentes, do próprio usuário, e nenhuma arquivada |
| RB-016 | A compra no cartão é despesa **na data da compra** (como o app já faz hoje); o pagamento da fatura nunca vira despesa |
| RB-017 | Fatura = soma das despesas ligadas ao ciclo − estornos (receitas na conta do cartão) |
| RB-018 | Pagamento maior que o saldo da fatura é rejeitado (crédito antecipado fica fora do escopo) |
| RB-019 | Compra feita até o dia de fechamento, **inclusive**, entra na fatura que fecha; o usuário pode mudar a fatura de uma compra |
| RB-020 | Limite disponível = limite − dívida do cartão (compras − estornos − pagamentos); passar do limite **avisa**, não bloqueia |
| RB-021 | Dias 29 a 31 de fechamento/vencimento viram o último dia do mês quando ele não existe |

## 6. Modelo de dados proposto

**Slice `transfers`** (nova, genérica):
- `transfers`: `id`, `user_id`, `from_account_id`, `to_account_id`, `amount` (> 0), `occurred_at`, `description`, `created_at`. Não mexe na tabela de lançamentos.

**Slice `credit_cards`** (nova):
- `credit_cards`: `id`, `user_id`, `account_id` (único, FK), `closing_day` (1–31), `due_day` (1–31), `credit_limit` (opcional), `default_payment_account_id` (opcional), `created_at`.
- `card_purchases`: `transaction_id` (único, FK), `credit_card_id`, `invoice_closing_date` — liga uma compra à **fatura escolhida**. Sem linha, a fatura é calculada pela data (compras antigas e as lançadas direto em `/transactions` continuam funcionando).
- `card_invoice_payments`: `id`, `credit_card_id`, `invoice_closing_date`, `transfer_id` (único, FK), `amount`, `paid_at`.

**Fatura (decisão 2):** não é uma tabela; é **calculada** a partir das compras ligadas ao ciclo e dos pagamentos.

**Dependências:** `transfers` → `accounts`; `credit_cards` → `accounts`, `transactions`, `transfers`, `categories`. Nenhuma slice existente passa a depender de `credit_cards`.

## 7. Matemática do ciclo (função pura, testável)

- **Fechamento do mês M:** dia `closing_day` (ajustado ao último dia do mês, RB-021).
- **Fatura de uma compra na data d:** a que fecha na primeira data de fechamento **≥ d** (RB-019, inclusive).
- **Vencimento da fatura:** a primeira data **depois** do fechamento cujo dia é `due_day`. Exemplo: fecha 5, vence 12 → mesmo mês; fecha 28, vence 5 → mês seguinte.
- **Situação:** *aberta* (ainda acumulando, fechamento ≥ hoje), *fechada* (fechou, saldo > 0, vencimento ≥ hoje), *vencida* (vencimento < hoje, saldo > 0), *paga* (saldo ≤ 0, ciclo encerrado).

## 8. API proposta

| Rota | O que faz |
|---|---|
| `POST/GET /transfers`, `DELETE /transfers/{id}` | Transferência entre contas |
| `POST/GET/PATCH /cards`, `GET /cards/{id}` | Cartão com limite usado/disponível |
| `POST /cards/{id}/purchases` | Compra (com `installments` e fatura opcional) |
| `GET /cards/{id}/invoices` | Faturas dos ciclos (passados, atual e futuros com compras) |
| `GET /cards/{id}/invoices/{closing_date}` | Compras do ciclo e pagamentos |
| `PATCH /cards/{id}/purchases/{transaction_id}` | Mudar a fatura de uma compra |
| `POST /cards/{id}/invoices/{closing_date}/payments` | Pagar fatura (cria a transferência) |
| `DELETE /cards/{id}/invoices/{closing_date}/payments/{id}` | Desfazer pagamento |
| `GET /cards/summary` | Faturas vencidas e a vencer, para o alerta |

## 9. Esforço (por analogia, não medido)

| Parte | Horas |
|---|---|
| `transfers`: modelo, migration, serviço, API, testes, tela básica | 6–10 |
| `credit_cards` backend: ciclo, compras, parcelas, faturas, pagamento, limite, testes | 14–22 |
| Frontend: cartões, compra, fatura, pagamento, alerta | 10–16 |
| **Total** | **30–48 h** (confiança média-baixa) |

A faixa é larga porque as **regras de cada banco** (fechamento, horário de corte) são a maior incerteza. **DESCONHECIDO:** a sua disponibilidade semanal.

## 10. Riscos

| Risco | Mitigação |
|---|---|
| Regra de fechamento diferente da do seu banco | RB-019 documentada, fatura escolhível por compra, e validação com o **seu cartão real** (pergunta na decisão 3) |
| Contar a compra duas vezes | RB-014/RB-016 + teste que compara o dashboard antes e depois de pagar a fatura |
| Parcelas futuras poluírem o dashboard | O dashboard já filtra por período; parcelas só aparecem no mês em que vencem |
| Compras antigas em contas de cartão não terem fatura ligada | Fallback: sem vínculo, a fatura é calculada pela data |
| Escopo (juros, rotativo, adiantamento) crescer | Fora do escopo, explicitado na seção 4 |

## 11. Decisões

> **(confirme)**: recomendação clara, basta "ok". **(escolha)**: depende de preferência sua.

### DECISÃO 1 (escolha) — Como representar o pagamento da fatura
- **ALTERNATIVAS:** (a) **transferência** como conceito próprio (slice `transfers`); (b) novo valor `transfer` em `TransactionType`; (c) tratar o pagamento como despesa e **ignorar** as compras do cartão nos totais (regime de caixa).
- **EVIDÊNCIAS:** o código só tem receita/despesa e nenhum saldo por conta. (b) obrigaria mexer em dashboard, orçamentos, metas e importação. (c) esconde o gasto até a fatura ser paga (mês errado) e quebra o que o app já faz.
- **TRADE-OFFS:** (a) é uma slice nova, mas **não toca** a tabela de lançamentos nem nenhum total existente, e serve de base para patrimônio (Marco 12) e investimentos (Marco 13).
- **RECOMENDAÇÃO:** **(a)**.
- **CONFIANÇA:** Alta.

### DECISÃO 2 (escolha) — Fatura calculada ou gravada como conta a pagar
- **ALTERNATIVAS:** (a) fatura **calculada** a partir das compras (fonte única da verdade), aparecendo no alerta do dashboard e, no Marco 10, no fluxo de caixa; (b) a fatura vira uma **conta a pagar** do Marco 8 (compromisso) criada no fechamento.
- **EVIDÊNCIAS:** no Marco 8 a baixa de um compromisso cria uma **despesa**; para fatura precisaria criar uma transferência. (b) também duplica o total (na compra e no compromisso) e fica velho quando uma compra é lançada depois do fechamento.
- **TRADE-OFFS:** (a) significa que a fatura **não** aparece na tela de "A pagar/receber" (fica em Cartões, com alerta no dashboard); (b) unifica a lista, mas custa sincronização e uma exceção na baixa.
- **RECOMENDAÇÃO:** **(a)**; o Marco 10 consome contas a pagar **e** faturas.
- **CONFIANÇA:** Média-alta.

### DECISÃO 3 (escolha, com uma pergunta) — Regra de fechamento
- **Proposta:** compra até o dia de fechamento, **inclusive**, entra na fatura que fecha; o usuário pode mover a compra para outra fatura (como no Mobills).
- **EVIDÊNCIAS:** o dia do fechamento é ambíguo e varia por banco e horário.
- **PERGUNTA PARA VOCÊ:** qual é o **banco**, o **dia de fechamento** e o **de vencimento** do(s) seu(s) cartão(ões)? Com uma fatura real sua eu valido a regra antes de implementar.
- **CONFIANÇA:** Média (sobe com um exemplo real).

### DECISÃO 4 (confirme) — Compra parcelada
- **ALTERNATIVAS:** (a) N despesas com data em cada fatura, descrição "(i/N)"; (b) uma única despesa com parcelas "virtuais" calculadas.
- **RECOMENDAÇÃO:** **(a)**. Cada parcela é um lançamento normal, entra no dashboard no mês certo e pode ser editada. O limite considera todas as parcelas (como no banco).
- **CONFIANÇA:** Alta.

### DECISÃO 5 (confirme) — Quando a despesa conta
- **RECOMENDAÇÃO:** **na data da compra** (já é o comportamento atual), e o pagamento da fatura nunca conta. O fluxo de caixa (Marco 10) usa o **vencimento da fatura**, então as duas visões ficam consistentes.
- **CONFIANÇA:** Alta.

### DECISÃO 6 (escolha) — Pagamento parcial da fatura
- **ALTERNATIVAS:** (a) o saldo **continua na mesma fatura** como dívida; juros o usuário lança como despesa no cartão; (b) estilo Mobills: fecha a fatura e cria uma despesa do restante na seguinte.
- **TRADE-OFFS:** (b) cria despesa artificial que dobra o gasto; (a) é simples e fiel ao que acontece (a dívida continua).
- **RECOMENDAÇÃO:** **(a)**.
- **CONFIANÇA:** Média.

### DECISÃO 7 (confirme) — Limite
- **RECOMENDAÇÃO:** o limite é informado por você, opcional; ultrapassar **avisa** e não bloqueia (o banco é quem bloqueia).

### DECISÃO 8 (confirme) — Interface
- **RECOMENDAÇÃO:** tela funcional com os componentes atuais, como no Marco 8; o visual vem na trilha separada.

## 12. Plano de execução (depois da aprovação)

1. `transfers`: modelo, migration, serviço, API e testes (inclui teste de que o dashboard não muda).
2. `credit_cards`: cadastro e a **função pura do ciclo** (fechamento/vencimento) com testes de borda (dia 29–31, virada de ano).
3. Compras no cartão e parcelamento.
4. Faturas calculadas (lista e detalhe) e limite.
5. Pagamento da fatura (transferência) e desfazer.
6. Resumo para o alerta do dashboard.
7. Frontend e verificação no navegador.

---

**STATUS:** Ainda não pronto.

**PENDÊNCIAS:** decisões **1, 2, 3 e 6** (as de escolha), a pergunta da decisão 3 (banco e datas do seu cartão) e um "ok" nas **4, 5, 7 e 8**.
