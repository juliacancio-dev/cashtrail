# CashTrail — Marco 12: Patrimônio e balanço pessoal (desenho)

> Quinto marco da fase "ERP pessoal" ([22](22-erp-pessoal-discovery.md)); depende dos saldos por conta (Marco 10, [25](25-marco-10-fluxo-de-caixa-e-dre.md)), de cartões (Marco 9, [24](24-marco-9-cartoes-e-faturas.md)) e dívidas (Marco 11, [26](26-marco-11-dividas-e-financiamentos.md)). Segue o fluxo do projeto: **desenho e decisões antes de qualquer código**. Nada aqui foi implementado.

Legenda: **FATO** (código verificado) · **INFERÊNCIA** (conclusão minha) · **HIPÓTESE** · **DESCONHECIDO**.

## 1. Objetivo e critério de saída

**Objetivo:** responder "quanto eu valho hoje e como isso evoluiu?": **ativos − passivos = patrimônio líquido**, com a lista do que compõe cada lado e a evolução mês a mês.

**Critério de saída:**
1. O patrimônio de hoje = (saldo das contas de caixa + valor dos bens) − (dívida de cartão + saldo devedor das dívidas), e bate com a soma manual dos itens da tela.
2. Pagar parcela de empréstimo, pagar fatura ou transferir entre contas **não muda** o patrimônio por si só (só juros e despesas mudam), a menos que o valor do bem mude.
3. A evolução mostra o patrimônio no fim de cada mês dos últimos 12, calculado do histórico, sem snapshots manuais.
4. Um financiamento mostra o bem, a dívida e o **patrimônio líquido do bem** (valor − saldo devedor).

## 2. O que já existe (FATO — o código)

- `reports.balances(db, user, today)` já calcula o saldo de **qualquer data**: inicial + receitas − despesas + transferências até `today`. Serve de base para o patrimônio "em uma data".
- Contas de caixa = tipos fora de `NON_CASH_TYPES` (cartão e `loan`). Dívida de cartão e de empréstimo já saem separadas (`card_debt_total`, `loan_debt_total`).
- **Não existe** cadastro de bens (imóvel, carro etc.) nem valor de bem no tempo.
- Investimentos são o Marco 13: o balanço precisa **ter lugar para eles** sem retrabalho.

## 3. Pesquisa (o que o balanço pessoal costuma ter)

**INFERÊNCIA (contabilidade pessoal padrão, não verificado em fonte específica de app):**
- **Ativos**: circulantes (caixa, contas, aplicações de liquidez imediata) e não circulantes (imóveis, veículos).
- **Passivos**: de curto prazo (cartão, parcelas até 12 meses) e de longo prazo (saldo restante de financiamentos).
- Bens são avaliados por **valor de mercado estimado** (o usuário informa), não por custo; o valor muda ao longo do tempo (carro desvaloriza, imóvel valoriza).
- **DESCONHECIDO / fora do escopo:** consulta automática de valor (FIPE, avaliação de imóvel). Seria fonte externa (como as cotações do Marco 13); aqui o valor é **informado à mão**.

## 4. Escopo proposto

**Dentro:** cadastro de bens com histórico de avaliações; vínculo opcional bem ↔ dívida; balanço patrimonial de hoje (ou de uma data) com ativos e passivos agrupados; patrimônio líquido; evolução mensal; patrimônio líquido por bem financiado; exportação CSV (padrão do Marco 10); resumo no dashboard.

**Fora:** valor automático de bens (FIPE etc.); depreciação calculada; investimentos (Marco 13); IRPF (Marco 14); bens em copropriedade/percentual; moeda estrangeira.

## 5. Requisitos propostos

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RF-041 | Cadastrar bem (nome, tipo, data e valor de aquisição, avaliação atual) | Valor > 0; tipos: imóvel, veículo, outro |
| RF-042 | Atualizar a avaliação de um bem (histórico por data) | Valor do bem "em uma data" = última avaliação até essa data |
| RF-043 | Vincular bem a uma dívida (opcional) | Só dívida do próprio usuário; um bem tem 0 ou 1 dívida |
| RF-044 | Balanço patrimonial em uma data | Ativos (caixa, bens) e passivos (cartões, dívidas) com totais; PL = ativos − passivos |
| RF-045 | Evolução do patrimônio (meses) | PL de cada fim de mês recalculado do histórico |
| RF-046 | Patrimônio líquido por bem | Valor do bem − saldo devedor da dívida vinculada |
| RF-047 | Exportar balanço em CSV | Mesmas regras de segurança do CSV do Marco 10 |
| RF-048 | Resumo no dashboard | Patrimônio líquido e variação do mês |

| ID | Regra de negócio |
|---|---|
| RB-028 | Patrimônio líquido = Σ saldos das contas de caixa + Σ valor dos bens − Σ dívida de cartão − Σ saldo devedor das dívidas |
| RB-029 | Transferência entre contas e pagamento de fatura/parcela não alteram o patrimônio por si só (RB-014, RB-023) |
| RB-030 | O valor de um bem antes da primeira avaliação é zero (não aparece no balanço daquela data) |
| RB-031 | O balanço de uma data usa só movimentações até aquela data |

## 6. Decisões

### DECISÃO 1 — Como guardar o valor dos bens

- **ALTERNATIVAS:** **(a)** `assets` + `asset_valuations` (histórico por data); **(b)** `assets` com um único "valor atual", editável.
- **EVIDÊNCIAS:** RF-045 exige o patrimônio de meses passados; com (b) ele usaria sempre o valor de hoje e a evolução seria falsa (um carro "valia" o mesmo há um ano).
- **TRADE-OFFS:** (a) dá evolução correta e gráfico do valor do bem; custo: mais uma tabela e uma tela de avaliações. (b) é mais simples, mas a evolução do patrimônio fica enganosa.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Alta.

### DECISÃO 2 — Relação bem ↔ dívida

- **ALTERNATIVAS:** **(a)** vínculo opcional `asset.debt_id` (informativo: dá o PL por bem); **(b)** sem vínculo, bens e dívidas independentes.
- **EVIDÊNCIAS:** financiamento de carro/imóvel é o caso real; sem vínculo, o balanço soma certo mas não mostra "quanto do carro é meu".
- **TRADE-OFFS:** (a) não muda nenhum total (só agrega leitura) e custa uma coluna; (b) é zero custo, perde RF-046.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Alta.

### DECISÃO 3 — Evolução do patrimônio: calcular ou guardar

- **ALTERNATIVAS:** **(a)** calcular no ato, repetindo o saldo por data para cada fim de mês, mais avaliações e dívidas na data; **(b)** tabela de snapshots mensais gravados por job.
- **EVIDÊNCIAS:** `balances` já aceita data; o histórico é a fonte da verdade. Snapshots podem divergir quando o usuário corrige um lançamento antigo.
- **TRADE-OFFS:** (a) sempre consistente, sem job novo; custo: processa o histórico a cada pedido (12 meses; aceitável para uso pessoal, **a medir** com muito histórico). (b) é rápido, mas cria dado derivado que precisa ser invalidado e recalculado.
- **RECOMENDAÇÃO:** **(a)**; se ficar lento, otimizo com um único passe pelo histórico em vez de uma consulta por mês. **CONFIANÇA:** Média-alta.

### DECISÃO 4 — Como apresentar o balanço

- **ALTERNATIVAS:** **(a)** duas colunas ativos × passivos, com grupos (Caixa e contas, Bens | Cartões, Dívidas), curto × longo prazo nas dívidas e um espaço reservado para investimentos (Marco 13); **(b)** só uma lista plana com o total.
- **TRADE-OFFS:** (a) é o formato esperado de um balanço e acomoda o Marco 13 sem retrabalho; custo: separar curto/longo prazo exige somar o principal das parcelas dos próximos 12 meses (dado que já temos). (b) é trivial, mas mostra pouco.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Média-alta (curto × longo prazo é o ponto menos certo).

## 7. Modelo de dados proposto

- `assets`: `id`, `user_id`, `name`, `kind` (String + CHECK: `real_estate|vehicle|other`, **não** enum nativo), `acquired_at`, `acquisition_value`, `debt_id` (FK opcional, `SET NULL`), `is_archived`.
- `asset_valuations`: `asset_id`, `valued_at`, `value`, `note`; única por (asset_id, valued_at).
- Nenhuma mudança em contas, lançamentos ou dívidas.

**Slice:** nova `assets` (CRUD + avaliações); a visão de balanço entra em `reports` (somente leitura), dependendo só dos `service` de `accounts`, `credit_cards`, `debts` e `assets`. Ninguém depende de `reports`.

## 8. Plano de implementação

1. Migração `assets` e `asset_valuations` (up/down/up/check; o teste de migração real já cobre erro de enum).
2. Slice `assets`: CRUD, avaliações, valor em uma data, vínculo com dívida.
3. `reports`: `net_worth(date)` com agrupamentos e `net_worth_history(months)`; CSV.
4. Frontend: `/assets` (lista, avaliações), `/net-worth` (balanço, evolução, PL por bem), resumo no dashboard.
5. Verificação no navegador e documentação.

## 9. Riscos

| ID | Risco | Mitigação |
|---|---|---|
| R-12.1 | Valor de bem informado à mão fica desatualizado e distorce o patrimônio | Mostrar a data da última avaliação no balanço e avisar quando passar de 12 meses |
| R-12.2 | Evolução lenta com muito histórico | Um passe só pelo histórico por pedido; medir antes de otimizar |
| R-12.3 | Saldo inicial de uma conta é "de hoje para trás": meses anteriores ao uso do app mostram só o saldo inicial | Documentar na tela; a evolução começa no mês do primeiro dado |
| R-12.4 | Dívida de cartão e fatura futura confundem o passivo | Passivo de cartão = dívida total da conta (compras já lançadas, inclusive parceladas futuras), como no Marco 9 |

## 10. Perguntas para a Julia

1. **Decisão 1:** histórico de avaliações por bem (recomendado) ou só um valor atual?
2. **Decisão 2:** vínculo opcional bem ↔ dívida (recomendado)?
3. **Decisão 3:** evolução calculada do histórico, sem snapshots (recomendado)?
4. **Decisão 4:** balanço em duas colunas com curto × longo prazo e espaço para investimentos (recomendado)?
5. Que **tipos de bem** você quer? (Proposta: imóvel, veículo, outro.)

**STATUS:** decisões 1 a 4 aprovadas como recomendadas (2026-10-15); tipos de bem: imóvel, veículo e outro.

**IMPLEMENTADO (2026-10-15):** backend (572 testes no total) e frontend (`/assets`, `/net-worth`, cartão de patrimônio no dashboard) verificados no navegador (caixa 2.000 + carro 30.000 − financiamento 10.000 = PL 22.000; nova avaliação para 28.000 leva o PL a 20.000; gráfico de 12 meses).

**Decisões ao codar:**
- Em vez de arquivar, o bem tem `disposed_at` (venda ou baixa): zera o valor a partir da data e preserva o histórico anterior. O dinheiro da venda entra por lançamento normal.
- Avaliação na mesma data corrige o valor (upsert); o bem mantém ao menos uma avaliação.
- Uma dívida financia no máximo um bem (`debt_id` único).
- Curto × longo prazo só para a data de hoje (usa as parcelas em aberto); em datas passadas o balanço mostra só o total.
- Data futura não é aceita no balanço.
- Antes do primeiro uso do app a evolução reflete só o saldo inicial das contas (R-12.3).
