# CashTrail — Marco 13: Investimentos (desenho)

> Sexto marco da fase "ERP pessoal" ([22](22-erp-pessoal-discovery.md), seção 5), depende do patrimônio (Marco 12, [27](27-marco-12-patrimonio-e-balanco.md)), das transferências (Marco 9, [24](24-marco-9-cartoes-e-faturas.md)) e do DRE (Marco 10, [25](25-marco-10-fluxo-de-caixa-e-dre.md)). Segue o fluxo do projeto: **desenho e decisões antes de qualquer código**. Nada aqui foi implementado.

Legenda: **FATO** (verificado agora, em fonte ou chamada real) · **INFERÊNCIA** (conclusão minha) · **HIPÓTESE** · **DESCONHECIDO**.

## 1. Objetivo e critério de saída

**Objetivo:** registrar a carteira (ações, FIIs, ETFs, renda fixa, Tesouro, fundos), saber **quanto vale hoje**, **quanto rendeu** e **quanto de proventos entrou**, e fazer o patrimônio (Marco 12) refletir o valor de mercado, sem contar nada em dobro.

**Critério de saída:**
1. Comprar 10 ações a R$ 20 tira R$ 200 do caixa e cria uma posição de custo R$ 200; o **patrimônio não muda** no ato da compra (caixa vira ativo).
2. Com a cotação a R$ 25, a posição vale R$ 250, o resultado não realizado é + R$ 50 (+25%), e o patrimônio sobe R$ 50.
3. Vender 5 ações a R$ 25 devolve R$ 125 ao caixa, e o **ganho realizado de R$ 25** aparece uma vez só (como receita financeira no DRE do mês).
4. Um dividendo de R$ 7 entra como receita financeira e some do "custo", sem alterar a quantidade.
5. A carteira mostra retorno total e o comparativo com o CDI do mesmo período.
6. Se a fonte de cotações cair, nada quebra: o sistema mostra a **última cotação conhecida** com a data dela, e dá para informar o valor à mão.

## 2. O problema central: três coisas diferentes que parecem "dinheiro"

**INFERÊNCIA (mesma lógica de RB-014 e RB-023):**
- **Aporte e compra** movem dinheiro de lugar (caixa → investimento). **Não** é despesa.
- **Valorização da cota** muda o patrimônio sem nenhum lançamento: é **marcação a mercado**, não receita realizada.
- **Ganho na venda e proventos** são receita financeira de verdade (entram no DRE); **perda na venda** é despesa financeira.

**FATO — o código hoje:**
- `transfers` já move dinheiro entre contas sem tocar no DRE (Marco 9); `accounts.type` é enum nativo (`CHECKING`, `SAVINGS`, `CREDIT_CARD`, `LOAN`; o Postgres guarda o **nome** do membro, ver teste de migração real); `NON_CASH_TYPES` centraliza o que não é caixa.
- O balanço (Marco 12) soma caixa + bens − cartões − dívidas e **não tem investimentos**: o desenho dele reservou o lugar.
- Categorias têm `dre_group` com `financial_revenue` e `financial_expense`, que são exatamente onde proventos e ganhos/perdas entram.

## 3. De onde vêm os dados (pesquisa verificada em 2026-10-15)

| Fonte | Para quê | O que foi verificado |
|---|---|---|
| **API do Banco Central (SGS)** | Índices: CDI, IPCA, Selic | **FATO (chamada real feita)**: `api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados/ultimos/3?formato=json` devolveu o CDI diário (0,050788 % a.d.); série 433 devolveu o IPCA mensal; sem autenticação. Exige filtro de datas (regra de março/2025) e janela de até 10 anos por consulta. |
| **brapi.dev (plano grátis)** | Cotação de ações, FIIs e ETFs | **FATO (página de preços + chamada real)**: 15.000 requisições/mês, 1 ativo por requisição, cotação atualizada a cada 30 min, histórico de 3 meses, 1 requisição simultânea. `GET /api/quote/PETR4` respondeu sem token (o sandbox lista PETR4, VALE3, MGLU3, ITUB4); **os demais ativos aparentemente exigem token, não confirmado na página**. |
| **Tesouro Direto** | Preço e taxa dos títulos | **FATO (pesquisa)**: o Tesouro Transparente publica CSV com histórico desde 2004 (licença ODbL), com arquivo de centenas de MB e **sem o valor do dia**. Cotação atual só pela página do Tesouro ou por API de terceiros. |
| Renda fixa privada (CDB, LCI/LCA) | Valor atual | **DESCONHECIDO / INFERÊNCIA**: não há cotação pública por papel; o valor vem do extrato do banco (informado) ou de uma estimativa por % do CDI. |

**DESCONHECIDO:** termos de uso da brapi para uso pessoal (a página diz que planos pagos servem a produtos comerciais e remete aos termos; não li os termos). **Precisa ser verificado antes de depender dela em produção.**

**INFERÊNCIA (consumo):** uma carteira de 30 ativos atualizada uma vez por dia útil gasta ~660 requisições/mês, bem abaixo das 15.000. Atualizar a cada abertura de tela estouraria o limite com facilidade; por isso o desenho usa cache e atualização controlada.

## 4. Escopo proposto

**Dentro:**
- Cadastro de ativos por classe: ação, FII, ETF, BDR, renda fixa, Tesouro, fundo, cripto, outro.
- Contas do tipo `investment` (corretora/banco) para guardar o custo da carteira.
- Operações: compra, venda, provento (dividendo, JCP, rendimento) e ajuste de valor.
- Posição: quantidade, preço médio, custo, valor de mercado, resultado não realizado, proventos, retorno total.
- Cotação automática (brapi) para renda variável; valor informado para o resto; cache e última cotação conhecida.
- Comparativo com CDI (BCB) desde a primeira compra.
- Carteira no patrimônio (valor de mercado) e proventos/ganhos no DRE.

**Fora:**
- Imposto sobre ganho de capital, come-cotas, isenção de R$ 20 mil/mês (é o **Marco 14, IRPF**; as regras da Receita não foram verificadas).
- Desdobramentos, grupamentos e bonificações automáticos (v1: ajuste manual de quantidade).
- Rentabilidade ponderada pelo tempo (TWR/XIRR) e performance por período.
- Cotação em moeda estrangeira, opções, derivativos, cripto em tempo real.
- Importação de nota de corretagem ou extrato da B3.

## 5. Requisitos propostos

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RF-049 | Cadastrar conta de investimento e ativos (classe, símbolo opcional, fonte de cotação) | Ativo pertence a conta `investment` do usuário; símbolo único por usuário e conta |
| RF-050 | Registrar compra | Cria transferência caixa → conta de investimento do custo (+ corretagem); quantidade e preço médio atualizados |
| RF-051 | Registrar venda | Reduz a posição ao preço médio; devolve o **produto da venda** ao caixa; ganho ou perda vira lançamento financeiro |
| RF-052 | Registrar provento | Lançamento de receita financeira na conta de caixa; não altera quantidade nem custo |
| RF-053 | Posição e carteira | Custo, valor de mercado, resultado não realizado e retorno total por ativo e no total |
| RF-054 | Cotação com cache | Última cotação por ativo com data e fonte; falha da fonte não apaga nem bloqueia |
| RF-055 | Atualizar cotações (botão e job diário) | No máximo uma requisição por ativo por atualização; respeita limite mensal configurado |
| RF-056 | Valor manual (renda fixa, fundo, outro) | Registra "valor atual" com data; entra na carteira e no patrimônio |
| RF-057 | Comparativo com CDI | Rentabilidade acumulada da carteira × CDI acumulado desde a primeira compra |
| RF-058 | Carteira no balanço patrimonial | Valor de mercado dos investimentos entra nos ativos; ver RB-032 |

| ID | Regra de negócio |
|---|---|
| RB-032 | Patrimônio usa o **valor de mercado** dos investimentos, e **não** o saldo da conta `investment` (que é só o custo): o saldo dessas contas fica fora de "caixa" e fora do ativo, para não contar em dobro |
| RB-033 | Compra e aporte são transferências (RB-014): não alteram DRE nem resultado |
| RB-034 | Ganho na venda = produto − custo médio × quantidade vendida; ganho vira receita financeira, perda vira despesa financeira, no dia da venda |
| RB-035 | Provento é receita financeira no dia do pagamento; não reduz o custo médio |
| RB-036 | Custo médio por **média ponderada móvel**; corretagem e taxas da compra integram o custo |
| RB-037 | Valorização não realizada **não** vira lançamento e **não** entra no DRE |

## 6. Decisões

### DECISÃO 1 — Como a carteira se integra ao caixa e ao DRE

- **ALTERNATIVAS:**
  - **(a)** Conta do tipo `investment`: compra = transferência para ela (custo); venda = transferência do **custo** de volta + lançamento do ganho (ou perda); provento = receita. A carteira tem valor de mercado à parte.
  - **(b)** Investimento como **bem** do Marco 12 (com avaliações), sem operações.
  - **(c)** Operação gera um único lançamento de despesa/receita (como app simples de gastos).
- **EVIDÊNCIAS:** (a) usa só primitivas que já existem e já são verificadas (transferência neutra, `financial_revenue`/`financial_expense`, `NON_CASH_TYPES`); o saldo da conta vira o **custo** remanescente, que é uma informação útil e verificável.
- **TRADE-OFFS:** (a) é o desenho contábil correto e mantém DRE e fluxo de caixa honestos; custo: novo valor no enum nativo (mitigado pelo teste de migração real) e uma regra a mais para o balanço (RB-032). (b) é trivial, mas não tem quantidade, preço médio nem proventos, então não responde "quanto rendeu". (c) conta compra como despesa e erra o resultado.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Média-alta; a regra de venda (transferir custo + lançar ganho) é a parte que mais merece teste de propriedade.

### DECISÃO 2 — Fonte de cotações

- **ALTERNATIVAS:** **(a)** brapi (plano grátis) para renda variável + valor manual para o resto + BCB para índices, com cache e atualização controlada; **(b)** só manual; **(c)** fonte não oficial (ex.: scraping do Yahoo ou B3) sem contrato.
- **EVIDÊNCIAS:** seção 3. A brapi funciona sem token no sandbox e dentro do limite com folga; o BCB é oficial e aberto.
- **TRADE-OFFS:**
  - (a) automatiza o que importa (renda variável); custos: dependência externa, um **token** a guardar como segredo (nunca no frontend nem no repositório; local em `.env`, produção em segredo do GitHub/Azure, o que é uma etapa de Azure e fica para quando você liberar), e a validação pendente dos termos de uso. Falha da fonte é tratada com cache e última cotação.
  - (b) elimina dependência, mas a carteira vive desatualizada e ninguém mantém.
  - (c) frágil e potencialmente fora dos termos.
- **RECOMENDAÇÃO:** **(a)**, atrás de uma interface `QuoteProvider` para trocar de fonte sem refazer o resto. **CONFIANÇA:** Média (termos da brapi e necessidade de token por ativo não confirmados).

### DECISÃO 3 — Quando as cotações são atualizadas

- **ALTERNATIVAS:** **(a)** botão "atualizar" + job diário ao fim do pregão (reaproveita o agendador do Marco 7); **(b)** a cada abertura de tela; **(c)** só manual.
- **TRADE-OFFS:** (a) fica em ~660 requisições/mês para 30 ativos e é previsível; custo: o job é mais um agendamento a ligar na produção (mesma flag `ENABLE_SCHEDULER`). (b) estoura 15.000/mês com poucos acessos e deixa a tela lenta. (c) não depende de nada, mas ninguém lembra.
- **RECOMENDAÇÃO:** **(a)**, com teto mensal configurável de requisições. **CONFIANÇA:** Alta.

### DECISÃO 4 — Rentabilidade na v1

- **ALTERNATIVAS:** **(a)** retorno simples sobre o custo (valor + proventos + vendas − aportes) / aportes, e comparativo com o CDI acumulado desde a primeira compra; **(b)** rentabilidade ponderada pelo tempo / XIRR.
- **TRADE-OFFS:** (a) é fácil de conferir à mão e responde "estou ganhando do CDI?"; custo: é impreciso quando há muitos aportes em datas diferentes (**dizer isso na tela**). (b) é o correto para comparar, mas exige fluxo de caixa datado e testes de convergência, e é pouco necessário para uma carteira pessoal pequena.
- **RECOMENDAÇÃO:** **(a)** agora; (b) vira item de backlog. **CONFIANÇA:** Alta.

## 7. Modelo de dados proposto

- `accounts.type` ganha `INVESTMENT` (nome do membro, como `LOAN`).
- `investment_assets`: `id`, `user_id`, `account_id` (conta `investment`), `name`, `symbol` (nulo para renda fixa/manual), `asset_class` (String + CHECK, **não** enum nativo), `quote_source` (`brapi` | `manual`), `is_archived`.
- `investment_operations`: `asset_id`, `kind` (`buy` | `sell` | `income` | `adjust`), `occurred_at`, `quantity`, `unit_price`, `fees`, `amount` (valor da operação), `transfer_id` e `transaction_id` opcionais (ligação ao lançamento real que gerou), `category_id` (para provento e ganho).
- `investment_quotes`: `asset_id`, `quoted_on`, `price`, `source`, `fetched_at`; única por (`asset_id`, `quoted_on`). O histórico diário que o cache acumula serve ao patrimônio de meses passados.
- Índices: `BCB` não vira tabela; é consulta com cache curto em memória/banco.

**Slice:** nova `investments` (operações, posição, cotações, provider), dependendo só do `service` público de `accounts`, `transactions`, `transfers` e `categories`. `reports` (patrimônio) passa a ler o valor de mercado pelo `service` de `investments`. Ninguém depende de `investments` além de `reports` e `dashboard`.

## 8. Plano de implementação

1. Migração: valor `INVESTMENT` no enum + três tabelas (up/down/up/check + teste de migração real).
2. Posição e preço médio: funções puras com testes de propriedade (média móvel, venda parcial, custo restante).
3. Operações: compra (transferência), venda (transferência do custo + ganho/perda), provento (receita) e desfazer.
4. `QuoteProvider`: brapi com cache, timeout, tratamento de limite/erro, valor manual; testes com provider falso (**nenhum teste chama a rede**).
5. Job diário + botão de atualizar; contador de requisições do mês.
6. BCB: CDI acumulado e comparativo.
7. Patrimônio: investimentos pelo valor de mercado (RB-032) e histórico pelas cotações guardadas.
8. Frontend: carteira, detalhe do ativo, nova operação, atualizar cotações, comparativo; patrimônio e dashboard.
9. Verificação no navegador e documentação.

## 9. Riscos

| ID | Risco | Mitigação |
|---|---|---|
| R-13.1 | Termos de uso ou limite da brapi mudam, ou exigem token para todos os ativos | `QuoteProvider` abstrato; valor manual sempre disponível; validar termos antes do deploy |
| R-13.2 | Token vazar (repositório, frontend, log) | Só no backend, via variável de ambiente; nunca logado; segredo do GitHub/Azure na etapa de deploy |
| R-13.3 | Venda registrar ganho errado (média, arredondamento, venda maior que a posição) | Teste de propriedade; venda acima da quantidade é rejeitada; arredondamento por operação |
| R-13.4 | Dobrar patrimônio (saldo da conta `investment` + valor de mercado) | RB-032 testada: conta `investment` fora de caixa e fora do ativo; teste de patrimônio com compra e valorização |
| R-13.5 | Cotação desatualizada passa despercebida | Mostrar a data da cotação e avisar quando passar de 3 dias úteis |
| R-13.6 | Desdobramento/bonificação distorce quantidade e preço médio | Fora da v1; ajuste manual de quantidade com aviso |
| R-13.7 | Enum nativo mais um valor (já houve erro de caixa) | Valor `INVESTMENT` em maiúsculas; teste de migração real já cobre todo `AccountType` |

## 10. Perguntas para a Julia

1. **Decisão 1:** conta `investment` com compra como transferência e ganho/perda como lançamento (recomendado)?
2. **Decisão 2:** brapi (grátis) para renda variável, valor manual para o resto e BCB para o CDI (recomendado)? Isso implica **você criar uma conta/token na brapi quando formos usar de verdade**; para desenvolver e testar uso um provedor falso e o sandbox sem token.
3. **Decisão 3:** botão de atualizar + job diário (recomendado)?
4. **Decisão 4:** retorno simples + comparativo com CDI na v1 (recomendado)?
5. Quais **classes** você realmente tem hoje? (Proposta: ações, FIIs, ETFs, renda fixa e Tesouro, fundos; cripto como "outro" manual.)

**STATUS:** decisões 1 a 4 aprovadas como recomendadas (2026-10-15). Classes não informadas: usada a proposta (ação, FII, ETF, BDR, renda fixa, Tesouro, fundo, cripto, outro).

**IMPLEMENTADO (2026-10-15):** backend (637 testes no total) e frontend (`/investments`, bloco de investimentos em `/net-worth`, tipo `investment` em `/accounts`) verificados no navegador **com a brapi e o BCB reais**: PETR4 cotada pelo sandbox sem token, CDI acumulado do BCB, compra de 10 a R$ 20 (R$ 200 da corrente para a corretora), venda de 4 a R$ 30 com ganho de R$ 40 contado uma vez no DRE.

**Decisões ao codar:**
- Só a **última** operação do ativo pode ser desfeita e as operações precisam ser cronológicas: caso contrário o custo médio de vendas já lançadas mudaria retroativamente.
- Taxas da compra integram o custo e aparecem como resultado não realizado negativo (o patrimônio cai o valor das taxas). Taxas da venda reduzem o produto e o ganho.
- A compra grava uma cotação `trade` (preço da operação) quando não há cotação do dia: dá o primeiro ponto do histórico do patrimônio.
- Renda fixa e fundos: cotação manual com quantidade 1 e o valor aplicado, atualizando o valor atual.
- Job diário (`ENABLE_SCHEDULER`) atualiza a carteira de todos; exceção da fonte externa nunca derruba a API.
- O token (`BRAPI_TOKEN`) é só do backend, nunca vai em erro nem em log (teste); sem token a brapi atende só ativos de teste.
- **Pendente antes de produção:** ler os termos de uso da brapi e criar o token (etapa de Azure, adiada).
