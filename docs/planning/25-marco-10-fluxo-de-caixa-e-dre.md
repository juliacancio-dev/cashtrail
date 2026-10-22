# CashTrail — Marco 10: Fluxo de caixa e DRE (desenho)

> Terceiro marco da fase "ERP pessoal" ([22](22-erp-pessoal-discovery.md)). Depende dos Marcos 8 ([23](23-marco-8-contas-a-pagar-receber.md)) e 9 ([24](24-marco-9-cartoes-e-faturas.md)). Segue o fluxo do projeto: **desenho e decisões antes de qualquer código**. Nada aqui foi implementado.

Legenda: **FATO** (fonte ou código verificado) · **INFERÊNCIA** · **HIPÓTESE** · **DESCONHECIDO** / **NÃO ENCONTRADO**.

## 1. Objetivo e critério de saída

**Objetivo:** responder duas perguntas diferentes com os dados que já existem.
- **DRE — "como foi o meu mês?"** receitas, despesas por tipo e o resultado, comparado com o mês anterior.
- **Fluxo de caixa — "quanto dinheiro tenho e vou ter?"** saldo inicial, o que entrou e saiu, saldo final, **previsto × realizado**, e a projeção dos próximos meses.

**Critério de saída:** (1) o resultado do DRE de um mês bate com receitas − despesas lançadas no mês, sem contar transferências; (2) o saldo final do fluxo de caixa bate com a soma dos saldos das contas; (3) uma compra de R$ 300 no cartão aparece **no DRE na data da compra** e **no fluxo de caixa só quando a fatura é paga**; (4) uma conta a pagar aparece como **previsto** no mês do vencimento e como **realizado** no mês em que foi paga.

## 2. Por que são dois relatórios (e não um)

**FATO** ([Conta Azul — visão de competência × visão de caixa](https://ajuda.contaazul.com/hc/pt-br/articles/4410825481869-Diferen%C3%A7as-entre-Vis%C3%A3o-de-Compet%C3%AAncia-e-Vis%C3%A3o-de-Caixa), [Linx](https://share.linx.com.br/display/CALCADOSPUB/19.+FINANCEIRO:+Fluxo+de+Caixa+Realizado+no+SetaERP+-+Cal%C3%A7ados)):
- **DRE** usa **competência**: registra a receita ou despesa quando ela acontece, mesmo que o pagamento venha depois.
- **Fluxo de caixa** usa **caixa**: só conta quando o dinheiro entra ou sai de fato.
- Exemplo da própria ajuda: uma venda feita em 30/08 e recebida em 10/09 está em agosto na competência e em setembro no caixa.

**INFERÊNCIA para o CashTrail:** o cartão de crédito é o caso mais claro. Uma compra de R$ 300 em março é despesa de **março** no DRE; o dinheiro só sai da conta quando a fatura é paga, em **abril**. Os dois relatórios dão números diferentes para o mesmo mês, e os dois estão certos.

**FATO — como o Conta Azul monta o fluxo mensal** ([como interpretar](https://ajuda.contaazul.com/hc/pt-br/articles/8603429895309-Como-interpretar-o-Fluxo-de-caixa-mensal-na-Conta-Azul), [previsto e realizado](https://ajuda.contaazul.com/hc/pt-br/articles/45430656970381-Relat%C3%B3rios-financeiros-como-os-valores-previstos-e-realizados-s%C3%A3o-calculados-no-Fluxo-de-caixa-mensal)):
- Colunas **Previsto** (usa a data de **vencimento**, valor bruto) e **Realizado** (usa a data da **baixa**, valor efetivo).
- Estrutura: saldo inicial, entradas, saídas, transferências entre contas, saldo final por mês, diferença previsto × realizado.
- Um recebimento previsto para janeiro e pago em março aparece em janeiro no previsto e em março no realizado.
- Dá para clicar num valor e ir à lista que o compõe (extrato, contas a pagar/receber).
- No gráfico de saldo, **linha contínua = realizado, tracejada = previsto**.

**NÃO ENCONTRADO:** nenhuma fonte específica de DRE **pessoal**; todas tratam de empresas. A estrutura da seção 5 é uma adaptação minha, baseada na estrutura empresarial (receita bruta → deduções → custos → despesas → resultado).

## 3. O que existe hoje no CashTrail (FATO — código lido)

- **Categorias:** só `name` e `is_archived`. **Não têm tipo nem grupo**, então hoje não dá para dizer que "Aluguel" é despesa fixa e "Mercado" é variável.
- **Contas:** não têm **saldo inicial** nem saldo calculado. A busca por "balance/saldo" na slice `accounts` não acha nada.
- **Dashboard:** soma receitas e despesas do período e mostra um "saldo do período" (receitas − despesas). Isso **não** é o saldo das contas.
- **Transferências e cartões** (Marco 9) já existem; **contas a pagar** (Marco 8) também.
- `transactions` é a fonte de tudo que foi realizado; não depende de nenhuma slice nova.

## 4. Escopo

**Dentro:** saldo inicial e saldo atual por conta; grupo de DRE nas categorias; DRE do período; fluxo de caixa mensal previsto × realizado; projeção dos próximos meses; detalhe dos itens por trás de cada número; exportar CSV (opcional, decisão 6).

**Fora:** DRE por centro de custo, orçamento × realizado dentro do fluxo (já existe em Orçamentos), fluxo diário/semanal, projeção estatística de gastos variáveis (média histórica), conciliação bancária (importação já existe), balanço patrimonial (Marco 12).

## 5. Estrutura do DRE pessoal (adaptação, decisão 1)

| Linha | O que entra |
|---|---|
| (+) **Receitas** | salário, freelas, aluguel recebido |
| (−) **Deduções** | descontos em folha (INSS, IR retido) |
| (=) **Receita líquida** | |
| (−) **Despesas variáveis** | mercado, lazer, transporte por app |
| (=) **Resultado bruto** | |
| (−) **Despesas fixas** | aluguel, condomínio, luz, internet, plano de saúde |
| (=) **Resultado operacional** | |
| (−) **Despesas financeiras** | juros, tarifas, IOF |
| (+) **Receitas financeiras** | rendimento de aplicações |
| (=) **Resultado do mês** | sobra ou falta |

Cada linha mostra o valor, o **% da receita líquida** e a **variação contra o período anterior**. Período anterior (corrigido em 2026-10-22): se o período são **meses inteiros**, o mesmo número de meses inteiros logo antes (outubro → setembro; out–dez → jul–set); senão, o mesmo número de dias terminando na véspera. Antes era sempre o mesmo número de dias, e outubro era comparado com 31/08 a 30/09.

**FATO — como o Bling resolve:** a categoria financeira tem um **"grupo do DRE"** ([ajuda do Bling](https://ajuda.bling.com.br/hc/pt-br/articles/360036734714-Como-incluir-uma-conta-a-pagar), seção de cadastros). Sem esse agrupamento, o DRE não fecha.

## 6. Regras de cálculo

**Contas de caixa** = contas que **não** são cartão de crédito. O cartão é tratado como dívida, não como dinheiro.

| ID | Regra |
|---|---|
| RB-022 | **DRE (competência):** usa a data do lançamento. Compra no cartão conta na data da compra. **Transferências não entram** (RB-014). |
| RB-023 | **Fluxo realizado (caixa):** lançamentos em contas de caixa + transferências que cruzam a fronteira caixa↔cartão (caixa→cartão é saída "pagamento de cartão"; cartão→caixa é entrada). **Compra no cartão não entra** na data da compra. Transferência entre duas contas de caixa não altera o fluxo. |
| RB-024 | **Previsto:** valor bruto na data de **vencimento**, mesmo que já tenha sido pago (padrão do Conta Azul). Fontes: contas a pagar/receber, faturas de cartão, recorrências futuras e lançamentos com data futura em contas de caixa. |
| RB-025 | **Atrasado:** item vencido e não pago aparece no previsto do mês de vencimento e, na projeção, é tratado como pendente no mês atual. |
| RB-026 | **Saldo:** saldo inicial + entradas − saídas = saldo final; o final de um mês é o inicial do seguinte. Saldo de uma conta = saldo inicial + receitas − despesas + transferências recebidas − enviadas. |
| RB-027 | A projeção **não inclui** compras futuras que ainda não foram lançadas no cartão (a tela avisa que subestima). |
| RB-028 | Categoria sem grupo cai em **"Sem grupo"**, destacada para ser classificada. |
| RB-029 | Lançamento no sentido oposto ao do grupo (ex: estorno em categoria de despesa) **abate** o total do grupo. |

## 7. Modelo de dados proposto (mudanças pequenas, nenhuma tabela nova)

- `accounts.opening_balance` — `Numeric(12,2)`, padrão 0 (decisão 3).
- `categories.dre_group` — texto com restrição de valores (`revenue`, `deduction`, `variable_expense`, `fixed_expense`, `financial_expense`, `financial_revenue`), nulo = "Sem grupo". **Texto com CHECK, e não enum do Postgres**: o projeto já teve problema duas vezes com enum novo em migration.

**Nova slice `reports`** (só leitura, como o `dashboard`): consome `accounts`, `categories`, `transactions`, `transfers`, `commitments`, `credit_cards` e `recurring` pelos `service` públicos. **Nenhuma slice depende dela.** O saldo por conta precisa viver aqui, porque `transactions` já depende de `accounts` (calcular o saldo dentro de `accounts` criaria dependência circular).

## 8. API proposta

| Rota | O que faz |
|---|---|
| `PATCH /accounts/{id}` | passa a aceitar `opening_balance` |
| `PATCH /categories/{id}` | passa a aceitar `dre_group` |
| `GET /reports/balances` | saldo por conta (cartão mostra dívida) e total em caixa |
| `GET /reports/dre?start_date&end_date&include_forecast` | linhas do DRE, % da receita, período anterior |
| `GET /reports/cash-flow?start_month&months` | colunas mensais: saldo inicial, previsto, realizado, saldo final, projetado |
| `GET /reports/cash-flow/items?month&direction&column` | itens que compõem cada número (detalhe) |

## 9. Esforço (por analogia, não medido)

| Parte | Horas |
|---|---|
| Saldo inicial e grupo de DRE (migration, serviço, API, testes) | 4–6 |
| `reports`: saldos, DRE e fluxo de caixa com projeção e detalhe (a parte mais delicada) | 18–28 |
| Frontend: página de DRE, página de fluxo com gráfico, edição de grupo/saldo, tela de saldos | 14–22 |
| Exportar CSV com proteção contra injeção de fórmula (opcional) | 3–5 |
| **Total** | **39–61 h** (confiança média-baixa) |

A faixa é larga porque as regras de cruzamento entre cartão, transferência e previsto têm muitos casos de borda. **DESCONHECIDO:** a sua disponibilidade semanal.

## 10. Riscos

| Risco | Mitigação |
|---|---|
| Contar o cartão duas vezes no fluxo (compra e pagamento) | RB-023 + teste que compara fluxo antes e depois de uma compra e de um pagamento |
| Saldo errado porque o usuário não informou o saldo inicial | A tela de Contas pede o saldo inicial e avisa quando está em zero com movimentações |
| DRE cheio de "Sem grupo" no começo | Tela de categorias com o grupo editável e aviso no relatório |
| Recorrência expandida duplicar algo que já virou compromisso | A expansão começa em `next_occurrence_date`, que é a primeira ocorrência **ainda não gerada** |
| Competência aproximada pelo vencimento (compromissos não têm data de competência) | Documentado; o Conta Azul recomenda uma data de competência separada, fica como evolução |
| "Hoje" no servidor é UTC | Mesmo limite já aceito no Marco 8 |

## 11. Decisões

> **(confirme)**: recomendação clara, basta "ok". **(escolha)**: depende de preferência sua.

### DECISÃO 1 (escolha) — Grupos do DRE
- **ALTERNATIVAS:** (a) DRE **simples**: receitas por categoria, despesas por categoria e o resultado, sem mudar o cadastro; (b) **grupos de DRE** nas categorias (os 6 da seção 5); (c) categorias **hierárquicas** (categoria dentro de grupo, definidos pelo usuário).
- **EVIDÊNCIAS:** o Bling usa "grupo do DRE" na categoria; uma fonte diz que sem plano de contas o DRE "não fecha". Hoje as categorias não têm nenhum atributo além do nome.
- **TRADE-OFFS:** (a) é o mais barato, mas devolve só uma lista de categorias, não um DRE de verdade. (c) é flexível demais para o que se precisa agora (custa árvore, tela e migração). (b) dá a estrutura de ERP com um campo por categoria.
- **RECOMENDAÇÃO:** **(b)**.
- **CONFIANÇA:** Média-alta.

### DECISÃO 2 (confirme) — DRE por competência, fluxo por caixa
- **RECOMENDAÇÃO:** o DRE usa a data do lançamento (compra no cartão conta na compra); o fluxo de caixa usa a data do movimento de dinheiro (cartão só no pagamento da fatura). Um modo "incluir previsto" no DRE soma contas a pagar/receber em aberto, pela data de vencimento.
- **CONFIANÇA:** Alta.

### DECISÃO 3 (escolha) — Saldo das contas
- **ALTERNATIVAS:** (a) **saldo inicial por conta** (novo campo, padrão 0), permitindo saldo atual por conta e saldo absoluto no fluxo; (b) mostrar **só os movimentos** (entradas, saídas, resultado), sem saldo absoluto.
- **EVIDÊNCIAS:** o fluxo de caixa dos ERPs é "saldo inicial + entradas − saídas = saldo final". Sem saldo inicial não existe projeção de saldo ("vai faltar dinheiro em março?"), que é a pergunta principal do relatório. O saldo por conta também é base do balanço patrimonial (Marco 12).
- **TRADE-OFFS:** (a) exige que você informe o saldo de cada conta uma vez; (b) evita isso, mas o relatório perde a utilidade principal.
- **RECOMENDAÇÃO:** **(a)**.
- **CONFIANÇA:** Alta.

### DECISÃO 4 (escolha) — Recorrências na projeção
- **ALTERNATIVAS:** (a) **expandir** as regras de recorrência (também as que geram lançamento) em ocorrências futuras previstas; (b) projetar só o que **já existe** (contas a pagar/receber, faturas, lançamentos com data futura).
- **EVIDÊNCIAS:** recorrências que geram conta a pagar só criam o compromisso **31 dias antes**; as que geram lançamento só criam **na data**. Com (b) a projeção fica quase vazia além de ~1 mês.
- **TRADE-OFFS:** (a) dá uma projeção de verdade (aluguel e assinaturas dos próximos meses), ao custo de gerar itens "virtuais" sem duplicar o que já existe. (b) é simples e honesto, mas pouco útil.
- **RECOMENDAÇÃO:** **(a)**.
- **CONFIANÇA:** Média.

### DECISÃO 5 (confirme) — Granularidade e horizonte
- **RECOMENDAÇÃO:** mensal, com previsto × realizado como no Conta Azul, horizonte padrão de **6 meses** (máximo 24), com detalhe clicável de cada número. Fluxo diário/semanal fica de fora.
- **CONFIANÇA:** Alta.

### DECISÃO 6 (escolha) — Exportar CSV
- **ALTERNATIVAS:** (a) incluir exportação de DRE e fluxo em CSV, com **proteção contra injeção de fórmula** (células que começam com `=`, `+`, `-`, `@` são neutralizadas, como já previsto em [11-security.md](11-security.md)); (b) deixar de fora por enquanto.
- **TRADE-OFFS:** (a) é útil para levar para planilha, custa 3 a 5 horas e um teste de segurança; (b) mantém o marco menor.
- **RECOMENDAÇÃO:** **(a)** como **última etapa**, cortável se o tempo apertar.
- **CONFIANÇA:** Média.

### DECISÃO 7 (confirme) — Interface
- **RECOMENDAÇÃO:** páginas funcionais com os componentes atuais e os gráficos já usados (Recharts, seguindo a paleta validada do projeto); o visual novo vem na trilha separada.

### DECISÃO 8 (confirme) — Onde mora o cálculo
- **RECOMENDAÇÃO:** nova slice `reports`, só de leitura, como o `dashboard`; o saldo por conta aparece na tela de Contas via `GET /reports/balances`.

## 12. Plano de execução (depois da aprovação)

1. Saldo inicial nas contas e grupo de DRE nas categorias (migration, API, testes).
2. `reports`: saldos por conta.
3. `reports`: DRE (com comparação e "incluir previsto").
4. `reports`: fluxo de caixa realizado e previsto por mês.
5. `reports`: projeção (recorrências expandidas) e detalhe dos itens.
6. Frontend: edição de saldo inicial e grupo, página de DRE, página de fluxo com gráfico, verificação no navegador.
7. Exportar CSV (se a decisão 6 for sim).

---

**STATUS:** Aprovado pela Julia em 2026-10-09, todas as recomendações: decisão 1 = (b) grupos de DRE nas categorias; 2 = DRE por competência e fluxo por caixa; 3 = saldo inicial por conta; 4 = expandir recorrências na projeção; 5 = mensal, 6 meses, previsto × realizado; 6 = exportar CSV como última etapa; 7 = páginas funcionais agora; 8 = slice `reports` só de leitura.

**Decisões tomadas ao codar:**
- `opening_balance` vale para qualquer conta; num cartão, valor negativo = dívida inicial (a dívida do cartão passa a considerá-lo).
- Realizado = movimento com data ≤ hoje; lançamento com data futura em conta de caixa entra como **previsto**.
- Recorrência expandida numa conta de **cartão** é projetada no vencimento da fatura do ciclo daquela data (não na data da compra), coerente com RB-023.
- A exportação CSV é gerada no **backend** (`/reports/*.csv`), para a proteção contra injeção de fórmula ter teste automatizado.

**IMPLEMENTADO (2026-10-09):** backend (315 testes) e frontend (`/dre`, `/cash-flow`, saldo inicial em `/accounts`, grupo em `/categories`) prontos; verificado no navegador (saldo 4.300, projetado out 3.500 / nov 3.800, drill-down, CSV de DRE e fluxo). Não implantado no Azure (aguarda o lote de marcos).
