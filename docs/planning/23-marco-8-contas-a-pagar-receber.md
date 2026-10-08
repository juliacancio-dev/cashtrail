# CashTrail — Marco 8: Contas a pagar e a receber (desenho)

> Primeiro marco da fase "ERP pessoal" ([22-erp-pessoal-discovery.md](22-erp-pessoal-discovery.md)). Segue o fluxo do projeto: **desenho e decisões antes de qualquer código**. Nada aqui foi implementado.

Legenda: **FATO** (fonte ou código verificado) · **HIPÓTESE** (proposta minha) · **DESCONHECIDO**.

## 1. Objetivo e critério de saída

**Objetivo:** o usuário registra **o que vai pagar e o que vai receber, com vencimento**, e ao pagar/receber o sistema cria o **lançamento realizado** automaticamente. É a primeira peça de "integração de ponta a ponta": o compromisso (futuro) vira lançamento (realizado) sem digitar duas vezes.

**Critério de saída:** (1) um compromisso pago gera exatamente um lançamento, com o valor e a data reais; (2) um compromisso parcelado em N vezes mostra N vencimentos e cada um é baixado de forma independente; (3) o que está vencido aparece como atrasado sem ninguém marcar; (4) os totais a pagar/receber do período batem com a soma manual dos compromissos.

## 2. Como os ERPs resolvem isso (pesquisa)

**FATO — Bling** ([incluir conta a pagar](https://ajuda.bling.com.br/hc/pt-br/articles/360036734714-Como-incluir-uma-conta-a-pagar), [baixa de conta a pagar](https://ajuda.bling.com.br/hc/pt-br/articles/4414639307031-Como-dar-baixa-em-uma-conta-a-pagar), [baixa parcial](https://ajuda.bling.com.br/hc/pt-br/articles/4414620414871-Como-dar-baixa-parcial-em-uma-conta-a-pagar)):
- Campos obrigatórios: **fornecedor, vencimento e valor**. A forma de pagamento define para onde o dinheiro vai na baixa.
- **Situações:** em aberto, vencendo hoje, atrasada, paga, paga parcialmente (em dia ou atrasada).
- **Baixa total:** data do pagamento, conta financeira, categoria, juros/desconto/multa/tarifa, valor pago.
- **Baixa parcial:** informa o valor pago; a conta fica "paga parcialmente".
- Parcelamento (gerar N parcelas) e contas fixas recorrentes.

**FATO — Conta Azul** ([baixa parcial](https://ajuda.contaazul.com/hc/pt-br/articles/7184294182797-Lan%C3%A7amentos-financeiros-como-fazer-baixa-parcial), [despesa parcelada](https://ajuda.contaazul.com/hc/pt-br/articles/12035652167565-Conta-a-pagar-parcelada-como-editar), [renegociar](https://ajuda.contaazul.com/hc/pt-br/articles/27081378711437-Conta-a-pagar-como-renegociar-valores-em-aberto)):
- Na baixa parcial, **o saldo restante continua em aberto** até ser quitado ou renegociado; cada baixa aparece separada no extrato.
- **Relatórios e fluxo de caixa refletem só o valor realmente movimentado.**
- Em parcelas, dá para editar **uma** parcela, **todas**, ou renegociar só o saldo em aberto.
- Em recorrências, a edição tem escopo (só esta, esta + futuras não pagas, todas as abertas).
- Lição de interface: contas a pagar/receber usam a **data de vencimento**, o extrato usa a **data de baixa**; por isso totais podem divergir entre telas. O desenho precisa deixar as duas datas explícitas.

**FATO — o que existe no CashTrail hoje** (código lido):
- `transactions.create_transaction` exige conta e categoria e rejeita conta arquivada.
- `recurring` **gera lançamentos já realizados** (não compromissos) e só avança a data.
- A API de lançamentos **não tem exclusão nem edição** (só listar, criar, buscar).
- `TransactionSource` tem `manual`, `recurring`, `import`; `transactions` já tem FKs opcionais `goal_id` e `recurring_transaction_id` sem conhecer essas slices.
- O dashboard consome só `transactions` e `categories`.

## 3. Escopo do Marco 8

**Dentro:** compromissos a pagar e a receber; parcelamento; baixa (total e parcial) que gera o lançamento; situação calculada; listagem com filtros e totais; cancelar; alerta de vencimentos no dashboard.

**Fora (marcos seguintes):** fatura de cartão (Marco 9), projeção de fluxo de caixa e DRE (Marco 10), dívidas e financiamentos (Marco 11), cadastro de favorecidos, renegociação de saldo, conciliação automática de extrato.

## 4. Requisitos propostos (continuam a numeração de `03-requirements.md`)

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RF-014 | CRUD de compromissos a pagar e a receber (descrição, valor, vencimento, categoria, conta prevista opcional, observação) | Compromisso criado aparece na listagem com a situação correta |
| RF-015 | Parcelamento: criar N compromissos de uma vez, com vencimentos mensais | N parcelas criadas, numeradas "i/N", somando exatamente o valor total (sem sobrar centavo) |
| RF-016 | Baixa: registrar pagamento/recebimento com data, conta e valor realmente pago | Cria **um** lançamento realizado com o valor e a data da baixa |
| RF-017 | Baixa parcial: o saldo continua em aberto | Compromisso de R$ 100 com baixa de R$ 40 mostra saldo R$ 60 e situação "paga parcialmente" |
| RF-018 | Situação calculada: em aberto, vence hoje, atrasado, pago, pago parcialmente, cancelado | Compromisso aberto com vencimento ontem aparece como atrasado sem ação do usuário |
| RF-019 | Listagem com filtros (direção, situação, período de vencimento, categoria, conta) e totais | Totais do filtro batem com a soma manual |
| RF-020 | Cancelar compromisso (não apaga, mantém histórico) | Cancelado sai dos totais a pagar/receber |
| RF-021 | Alerta in-app de vencimentos (vencidos e próximos) no dashboard | Dashboard mostra "N vencidos, N vencem em 7 dias" (sem e-mail, como RF-008a) |
| RF-022 | Recorrência pode gerar compromisso em vez de lançamento (ver decisão 3) | Recorrência configurada para "compromisso" cria um compromisso aberto no vencimento |

| ID | Regra de negócio |
|---|---|
| RB-007 | Compromisso a pagar gera lançamento do tipo **despesa** na baixa; a receber gera **receita** |
| RB-008 | Saldo = valor − soma das baixas; **pago** quando o saldo chega a zero |
| RB-009 | "Atrasado" é **derivado** (saldo > 0 e vencimento < hoje); nunca é gravado |
| RB-010 | Baixa em conta arquivada é rejeitada (reaproveita RB-003) |
| RB-011 | Baixa nunca ultrapassa o saldo em aberto |
| RB-012 | A soma das parcelas é sempre igual ao valor total (a diferença de centavos vai na primeira parcela) |
| RB-013 | Compromisso cancelado ou totalmente pago não pode ter valor/vencimento alterados |

## 5. Modelo de dados proposto

**Nova slice `commitments`** (nome em inglês, como as demais; na interface: "Contas a pagar e receber"):

- `commitments`: `id`, `user_id`, `direction` (`payable` | `receivable`), `description`, `counterparty` (texto livre, opcional), `amount` (> 0), `due_date`, `category_id` (FK, RESTRICT), `account_id` (FK opcional, conta prevista), `notes`, `installment_group_id` / `installment_number` / `installment_count` (opcionais), `is_canceled`, `created_at`.
- `commitment_settlements` (baixas): `id`, `commitment_id` (FK, CASCADE), `transaction_id` (FK, o lançamento criado), `amount`, `paid_at`, `created_at`.
- **Em `transactions`:** nada novo no modelo além de, no máximo, um vínculo opcional `commitment_id` (mesmo padrão de `goal_id`/`recurring_transaction_id`; ver decisão 4).

**Dependências (regra do [09-vertical-slices.md](09-vertical-slices.md)):** `commitments` depende de `transactions`, `accounts` e `categories`, **nunca o contrário**. `dashboard` passa a consumir `commitments.service` (nova seta). A baixa cria o lançamento chamando `transactions.service`, sem inserir direto na tabela.

## 6. API proposta

| Rota | O que faz |
|---|---|
| `GET /commitments` | Lista com filtros (`direction`, `status`, `due_from`, `due_to`, `category_id`, `account_id`) + totais |
| `POST /commitments` | Cria um compromisso, ou N parcelas se `installments` > 1 |
| `GET/PATCH /commitments/{id}` | Detalhe e edição (regras RB-013) |
| `POST /commitments/{id}/settlements` | Baixa total ou parcial: cria o lançamento e a baixa na mesma transação |
| `POST /commitments/{id}/cancel` | Cancela |
| `GET /commitments/summary` | Totais e contagens de vencidos/próximos, para o dashboard |

## 7. Esforço (estimativa por analogia, não medida)

| Parte | Horas | Base da estimativa |
|---|---|---|
| Backend: modelo, migration, parcelamento, baixa, situação, filtros, testes | 10–16 | Marcos 4 e 5 (slices com regra e migration) |
| Frontend: lista com filtros, formulário, parcelamento, diálogo de baixa | 8–14 | Marcos 3 e 4 |
| Integração: alerta no dashboard + recorrência gerando compromisso | 4–8 | Marco 5 |
| **Total** | **22–38 h** | Média confiança |

**HIPÓTESE:** é a analogia com o que o [14-estimates.md](14-estimates.md) previu para os marcos parecidos, não o tempo real gasto. **DESCONHECIDO:** a sua disponibilidade atual por semana (o documento assume 3–6 h). Em calendário isso seria de cerca de 4 a 13 semanas nessa premissa.

## 8. Riscos

| Risco | Mitigação |
|---|---|
| Baixa parcial aumenta bastante a complexidade (duas tabelas, saldo derivado) | Testes dedicados de saldo; é a regra mais testada do marco |
| Soma das parcelas com arredondamento de centavos | RB-012 + teste com valores como R$ 100 em 3x |
| Mudar o comportamento da recorrência já em produção (Marco 5) | A opção nova só vale para recorrências criadas com ela; as existentes continuam como estão |
| Lançamento criado por engano na baixa não pode ser corrigido (API não exclui) | Decisão 8 |
| Migration com enum novo no Postgres já deu problema duas vezes no projeto | Decisão 4 evita criar valor novo de enum |
| Interface decidida no escuro | Decisão 7: tela funcional agora, visual depois |

## 9. Decisões

> As marcadas **(confirme)** têm recomendação clara e basta você dizer "ok". As marcadas **(escolha)** dependem de preferência sua.

### DECISÃO 1 (escolha) — Baixa parcial
- **ALTERNATIVAS:** (a) só baixa total, com valor pago editável (juros/desconto); (b) baixa parcial com tabela de baixas, saldo continua em aberto (como Bling e Conta Azul).
- **EVIDÊNCIAS:** ambos os ERPs pesquisados suportam (b). No cartão de crédito (Marco 9) pagar parte da fatura é comum.
- **TRADE-OFFS:** (b) custa uma tabela e a regra de saldo; (a) é bem mais simples, mas o saldo restante precisaria virar outro compromisso na mão.
- **RECOMENDAÇÃO:** **(b)**.
- **CONFIANÇA:** Média-alta.

### DECISÃO 2 (confirme) — Parcelamento
- **ALTERNATIVAS:** (a) cada parcela é um compromisso independente, ligadas por um id de grupo; (b) um compromisso "pai" com parcelas filhas.
- **RECOMENDAÇÃO:** **(a)**: cada parcela já é, por si, uma conta com vencimento e baixa própria, e a listagem fica uma tabela só. O grupo permite "ver todas as parcelas".
- **CONFIANÇA:** Alta.

### DECISÃO 3 (escolha) — Recorrência gera compromisso?
- **ALTERNATIVAS:** (a) manter como está (a recorrência cria lançamento já realizado); (b) trocar para sempre gerar compromisso; (c) **opção por recorrência**: "gerar como lançamento" (padrão, como hoje) ou "gerar como compromisso".
- **EVIDÊNCIAS:** no Conta Azul as recorrências geram contas a pagar/receber a serem baixadas. Mas uma assinatura debitada no cartão já está paga no dia.
- **TRADE-OFFS:** (b) muda o comportamento em produção; (c) preserva o que existe e dá o fluxo de ERP para quem quiser (aluguel, condomínio, internet).
- **RECOMENDAÇÃO:** **(c)**, como **última etapa** do marco, que pode ser cortada se o tempo apertar.
- **CONFIANÇA:** Média-alta.

### DECISÃO 4 (confirme) — Como ligar a baixa ao lançamento
- **ALTERNATIVAS:** (a) novo valor `commitment` em `TransactionSource`; (b) sem enum novo: o vínculo é a tabela de baixas (e, se quiser, um `commitment_id` opcional no lançamento).
- **EVIDÊNCIAS:** o projeto teve problema duas vezes com enum em migration (anotado na memória do projeto).
- **RECOMENDAÇÃO:** **(b)**: o lançamento criado na baixa usa `source = manual` e o vínculo fica em `commitment_settlements`.
- **CONFIANÇA:** Alta.

### DECISÃO 5 (confirme) — Categoria obrigatória
- **ALTERNATIVAS:** (a) obrigatória ao criar o compromisso; (b) escolhida só na baixa (como o Bling).
- **RECOMENDAÇÃO:** **(a)**: o fluxo de caixa projetado e o DRE (Marco 10) precisam da categoria **antes** do pagamento, e o lançamento exige categoria de qualquer forma.
- **CONFIANÇA:** Alta.

### DECISÃO 6 (confirme) — Favorecido
- **ALTERNATIVAS:** (a) campo de texto livre opcional (`counterparty`); (b) cadastro de favorecidos como entidade.
- **RECOMENDAÇÃO:** **(a)** agora; promover a entidade só se aparecer necessidade real (por exemplo, histórico por fornecedor).
- **CONFIANÇA:** Alta.

### DECISÃO 7 (escolha) — Interface
- **ALTERNATIVAS:** (a) esperar a decisão visual (ERP, prints) antes de construir a tela; (b) construir a tela **funcional** agora com os componentes atuais, e fazer o redesenho visual como trilha separada depois.
- **EVIDÊNCIAS:** a decisão visual está parada esperando prints de ERPs; o backend não depende dela.
- **TRADE-OFFS:** (b) pode exigir retrabalho de estilo depois, mas não de lógica (a lógica fica nos componentes de dados). (a) paralisa o marco.
- **RECOMENDAÇÃO:** **(b)**, começando pelo backend (que é a maior parte do valor).
- **CONFIANÇA:** Média-alta.

### DECISÃO 8 (escolha) — Desfazer uma baixa
- **ALTERNATIVAS:** (a) não existe na v1 (se errar, corrige manualmente fora do sistema); (b) "desfazer baixa" que apaga a baixa e o lançamento ligado a ela; (c) estorno com lançamento oposto.
- **EVIDÊNCIAS:** hoje a API não exclui nem edita lançamentos. (c) polui o DRE com receita e despesa falsas.
- **TRADE-OFFS:** (b) exige criar uma exclusão controlada em `transactions` (só para lançamentos ligados a baixa), mas é o que dá confiança num sistema financeiro: um clique errado não pode ser permanente.
- **RECOMENDAÇÃO:** **(b)**, limitado a lançamentos criados por baixa.
- **CONFIANÇA:** Média.

## 10. Plano de execução (depois da aprovação)

1. Migration + modelos + serviço de compromissos (criar, parcelar, situação derivada) + testes.
2. Baixa total/parcial criando o lançamento + testes de saldo e de isolamento por usuário (RNF-001).
3. Listagem com filtros e totais + resumo para o dashboard.
4. Frontend funcional (lista, formulário com parcelamento, diálogo de baixa) e verificação no navegador.
5. Desfazer baixa (decisão 8) e alerta no dashboard.
6. Recorrência gerando compromisso (decisão 3), por último.

Uma branch e um commit por etapa significativa.

---

**STATUS:** Aprovado pela Julia em 2026-10-08, todas as recomendações: decisão 1 = (b) baixa parcial; 2 = (a) parcelas independentes com id de grupo; 3 = (c) opção por recorrência, como última etapa; 4 = (b) sem enum novo; 5 = (a) categoria obrigatória; 6 = (a) favorecido em texto livre; 7 = (b) tela funcional agora, visual depois; 8 = (b) desfazer baixa limitado a lançamentos criados por baixa.

**Notas de implementação decididas ao codar:**
- "Hoje" usa a data do servidor (UTC). Entre 21h e 24h em Brasília, um compromisso que vence "hoje" já aparece como atrasado. Aceito por ora; corrigir com fuso `America/Sao_Paulo` exige o pacote `tzdata` na imagem.
- Data de pagamento no futuro é rejeitada (evita lançamento realizado "fantasma").
- Parcelamento: o valor informado é o **total**; centavos que sobram vão para a primeira parcela (RB-012).
- O alerta de vencimentos vem de `GET /commitments/summary` (o dashboard do frontend chama o endpoint), em vez de o dashboard do backend importar `commitments`.
