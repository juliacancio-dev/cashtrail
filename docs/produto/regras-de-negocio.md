# Regras de negócio

As regras que decidem **como o dinheiro é contado** no CashTrail. Elas valem para todas as telas e relatórios, e uma mudança que quebre qualquer uma delas é um bug, mesmo que os testes da slice passem.

Os identificadores entre parênteses (`RB-014`) são os mesmos citados nos comentários do código; a definição original de cada um está no [catálogo de requisitos](../referencia/requisitos.md). Os termos estão no [glossário](glossario.md).

## Tipos de conta

| Tipo | O que representa | É caixa? | Saldo significa |
|---|---|---|---|
| `checking`, `savings` | conta corrente, poupança, carteira | sim | dinheiro disponível |
| `credit_card` | cartão de crédito | não | dívida do cartão (negativo) |
| `loan` | empréstimo ou financiamento | não | saldo devedor (negativo) |
| `investment` | conta numa corretora | não | custo remanescente da carteira |

"Conta de caixa" é toda conta que **não** está em `NON_CASH_TYPES` (`accounts/models.py`). Saldos, fluxo de caixa, calendário e dashboard usam esse único predicado ([ADR-012](../decisoes/ADR-012-contas-nao-caixa.md)).

Saldo de uma conta = saldo inicial + receitas − despesas + transferências recebidas − transferências enviadas (RB-026, Marco 10). O saldo inicial (`opening_balance`) é o saldo no começo do uso do app; num cartão ou dívida, valor negativo é a dívida que já existia.

## 1. Contagem única

**Cada movimentação conta uma única vez.** Só o fato econômico entra no resultado: a compra, os juros, o provento, o prêmio do seguro. Mover dinheiro entre contas próprias não é ganho nem gasto.

São **transferências**, neutras no resultado (RB-014), e por isso ficam fora de dashboard, orçamentos, metas e DRE:

| Operação | Vira |
|---|---|
| Transferência entre contas | transferência |
| Pagamento de fatura do cartão | transferência caixa → cartão |
| Receber o dinheiro de um empréstimo | transferência dívida → caixa (RB-023, Marco 11) |
| Amortizar o principal de uma dívida | transferência caixa → dívida |
| Comprar investimento ou aportar | transferência caixa → investimento (RB-033) |
| Vender investimento (parte do custo) | transferência investimento → caixa |

Transferências sempre entre contas diferentes do mesmo usuário, nenhuma arquivada (RB-015). Todo teste que mexe em dashboard, DRE, fluxo ou patrimônio deve provar que nenhum valor foi contado duas vezes.

## 2. Cartão de crédito

- A **compra é despesa na data da compra**; o pagamento da fatura nunca é despesa (RB-016).
- Compra parcelada em N vezes vira **N despesas**, uma em cada fatura consecutiva, com "(i/N)" na descrição. Os centavos que sobram vão para a primeira parcela.
- A fatura é **calculada**, não gravada: soma das compras ligadas ao ciclo menos estornos (RB-017, [ADR-011](../decisoes/ADR-011-fatura-calculada.md)).
- A fatura é identificada pela **data de fechamento**. Compra até o dia do fechamento, **inclusive**, entra na fatura que fecha; o usuário pode mover uma compra para outra fatura (RB-019).
- Vencimento = primeira data estritamente depois do fechamento com o dia de vencimento configurado. Dias 29 a 31 viram o último dia do mês quando ele não existe (RB-021).
- Pagamento parcial: o saldo continua na **mesma** fatura; pagar mais que o saldo é rejeitado (RB-018).
- Limite disponível = limite − dívida do cartão (inclui parcelas futuras). Passar do limite **avisa**, não bloqueia (RB-020).
- Mudar o dia de fechamento mantém cada fatura no mesmo mês.

## 3. Contas a pagar e a receber

- A baixa de um compromisso cria **um** lançamento realizado: despesa se a pagar, receita se a receber (RB-007).
- Saldo = valor − soma das baixas; **pago** quando chega a zero (RB-008). Baixa parcial é permitida e nunca ultrapassa o saldo (RB-011).
- **Atrasado é derivado**, nunca gravado: saldo > 0 e vencimento < hoje (RB-009).
- Parcelamento cria compromissos independentes ligados por um id de grupo; a soma das parcelas é sempre o total, e a diferença de centavos vai na primeira (RB-012).
- Compromisso cancelado ou totalmente pago não pode ter valor nem vencimento alterados (RB-013). Cancelar não apaga: mantém o histórico e sai dos totais.
- "Desfazer baixa" apaga a baixa e o lançamento criado por ela, e só esse lançamento.
- Data de pagamento no futuro é rejeitada.
- Uma recorrência pode gerar **lançamento** (padrão) ou **compromisso**; no segundo modo, o compromisso nasce 31 dias antes do vencimento.

## 4. DRE e fluxo de caixa

Dois relatórios, duas perguntas ([ADR-013](../decisoes/ADR-013-dre-competencia-fluxo-caixa.md)):

| | DRE | Fluxo de caixa |
|---|---|---|
| Pergunta | quanto ganhei e gastei? | vai faltar dinheiro? |
| Regime | **competência**: data do lançamento (RB-022) | **caixa**: data em que o dinheiro se move (RB-023, Marco 10) |
| Compra no cartão | conta na data da compra | conta no vencimento da fatura (pagamento) |
| Transferência | nunca entra | só quando cruza a fronteira caixa ↔ não caixa |

**DRE**

- Cada categoria tem um grupo de DRE (`dre_group`): receitas, deduções, despesas variáveis, despesas fixas, despesas financeiras e receitas financeiras. Categoria sem grupo cai em "Sem grupo", destacada (RB-028, Marco 10).
- Lançamento no sentido oposto ao do grupo (um estorno numa categoria de despesa) **abate** o total do grupo (RB-029, Marco 10).
- Cada linha mostra o valor, o % da receita líquida e a variação contra o período anterior. Período de meses inteiros compara com o mesmo número de meses inteiros logo antes (outubro → setembro); senão, com o mesmo número de dias terminando na véspera.

**Fluxo de caixa**

- **Realizado:** movimento com data ≤ hoje em contas de caixa, mais transferências que cruzam a fronteira caixa ↔ cartão. Transferência entre duas contas de caixa não altera o fluxo.
- **Previsto:** valor bruto na data de vencimento, mesmo que já pago (RB-024). Fontes: contas a pagar e a receber, faturas, recorrências expandidas em ocorrências futuras e lançamentos com data futura.
- **Atrasado:** aparece no previsto do mês de vencimento e, na projeção, como pendente no mês atual (RB-025).
- **Projetado** = realizado + o que falta do previsto. Mensal, horizonte padrão de 6 meses (máximo 24).
- Saldo inicial + entradas − saídas = saldo final; o final de um mês é o inicial do seguinte (RB-026, Marco 10).
- A projeção **não inclui** compras ainda não lançadas no cartão nem gastos do dia a dia não agendados; a tela avisa que subestima (RB-027, Marco 10).

## 5. Calendário do dinheiro

A tela inicial ([ADR-020](../decisoes/ADR-020-calendario-como-tela-inicial.md)), calculada por `GET /reports/calendar` a partir do fluxo de caixa:

- Saldo no fim do dia *d* = saldo inicial + realizados até *d* + o que resta dos previstos entre hoje e *d*. Por isso o dia de **hoje** no calendário já desconta o que vence hoje ou está atrasado.
- O número grande do topo (`cash_today`) é **só o realizado** e é igual ao `cash_total` de `/reports/balances`.
- O fechamento do mês é igual ao `closing_projected` do fluxo de caixa; o mês seguinte abre onde este fechou.
- **Dia apertado:** os `ceil(dias/4)` menores saldos do mês (o quarto mais baixo). Se os empates no valor de corte passarem de um quarto do mês, só entram os dias abaixo dele. Mês sem variação não tem dia apertado.

## 6. Dívidas e financiamentos

- A dívida é uma conta `loan`; saldo devedor = −saldo da conta.
- O cronograma é gerado por Price, SAC, sem juros ou informado. A soma do principal das parcelas é igual ao principal da dívida, e a última parcela absorve o arredondamento.
- **Baixa da parcela** = transferência do **principal** para a conta da dívida + despesa dos **encargos** (parcela − principal), com grupo de DRE `financial_expense` por padrão (RB-023 e RB-024, Marco 11).
- Editar o valor de uma parcela em aberto muda só os encargos; o principal do cronograma não muda. Parcela paga não pode ser editada, só desfeita (RB-025, Marco 11).
- Parcela de dívida **não** pode ser paga, editada ou cancelada pelas rotas genéricas de `/commitments` (HTTP 409); use `/debts`. Parcelas de dívida são pagas inteiras.
- O saldo devedor nunca fica negativo (RB-026, Marco 11).
- **Amortização extra** regera as parcelas em aberto pelo mesmo sistema e taxa: por padrão reduz o prazo, com opção de reduzir a parcela. Parcelas editadas à mão voltam ao valor calculado, com aviso (RB-027, Marco 11). Não tem desfazer.
- Quitação antecipada paga o saldo devedor de principal, sem desconto de juros futuros.

## 7. Patrimônio

Patrimônio líquido = caixa + bens + investimentos − dívida dos cartões − saldo devedor das dívidas (RB-028, Marco 12).

- **Bens** valem a última avaliação até a data; antes da primeira avaliação valem zero (RB-030). Venda ou baixa (`disposed_at`) zera o valor a partir da data e preserva o histórico.
- **Investimentos** entram pelo **valor de mercado**. O saldo da conta `investment` (custo) fica de fora, para não contar duas vezes (RB-032).
- Transferências e pagamentos de fatura ou parcela não mudam o patrimônio por si só; os juros, sim (RB-029, Marco 12).
- O balanço de uma data usa só movimentações até aquela data (RB-031); data futura não é aceita.
- A evolução é **recalculada** do histórico a cada pedido ([ADR-014](../decisoes/ADR-014-patrimonio-calculado.md)). Antes do primeiro uso do app, ela reflete só os saldos iniciais.
- Um bem pode ser ligado a no máximo uma dívida, e vice-versa: o balanço mostra quanto do bem é seu.

## 8. Investimentos

- **Compra** = transferência caixa → conta de investimento pelo custo; corretagem e taxas integram o custo (RB-033, RB-036).
- **Custo médio** ponderado móvel (RB-036).
- **Venda** = transferência do **custo** de volta ao caixa + ganho (receita financeira) ou perda (despesa financeira), lançado **uma vez**, no dia da venda (RB-034). Taxas da venda reduzem o produto e o ganho.
- **Provento** = receita financeira no dia do pagamento; não altera quantidade nem custo (RB-035).
- **Valorização não realizada não é receita** e não entra no DRE (RB-037).
- Só a **última** operação de um ativo pode ser desfeita, e as operações precisam ser cronológicas; senão o custo médio de vendas já lançadas mudaria para trás.
- Rentabilidade = retorno simples sobre o custo, comparado com o CDI acumulado desde a primeira compra. É impreciso com muitos aportes em datas diferentes, e a tela diz isso.

## 9. Imposto de renda (IRPF)

O CashTrail é **apoio à declaração**: monta o dossiê, estima o imposto e apura a renda variável. Não substitui o programa da Receita, e toda tela de IRPF diz isso.

- Três regimes que **não se misturam**: declaração anual (tabela progressiva), ganho de capital em renda variável (DARF mensal, fora da base anual, RB-038) e rendimentos isentos.
- Salário, 13º, PLR e renda fixa vêm do **informe de rendimentos digitado**; o sistema não recalcula.
- Ações (swing trade): 15%, venda até R$ 20.000 no mês é isenta **naquele mês** (RB-039); prejuízo só compensa a mesma modalidade e acumula entre meses (RB-040).
- Day trade é só **sinalizado** (o sistema guarda a data, não o horário); ETF, BDR, cripto e fundos aparecem como "não apurado".
- Bens e direitos em 31/12 pelo **custo**, não pelo valor de mercado (RB-041).
- Tabelas e limites vêm de `tax/parameters/<ano>.json`, com fonte e data (RB-042, [ADR-016](../decisoes/ADR-016-parametros-fiscais-por-ano.md)).
- Nenhum CPF ou CNPJ de terceiro é armazenado; dependentes entram só pela quantidade (RB-043).
- As premissas ainda não verificadas em fonte oficial estão em [Integrações externas](../referencia/integracoes-externas.md#receita-federal) e aparecem na tela.

## 10. Seguros e independência financeira

- O prêmio é despesa do período cobrado (RB-044). Mensal vira uma recorrência que gera conta a pagar; anual vira uma conta a pagar na renovação. Renovar não muda o prêmio do ciclo anterior.
- Encerrar a apólice desativa a recorrência (mensal) ou cancela a conta a pagar em aberto (anual).
- A simulação é sempre em **valores reais** (poder de compra de hoje), com retorno real informado (RB-045).
- Patrimônio-alvo = (renda desejada − benefício público esperado) × 12 ÷ taxa de retirada (RB-046).
- O progresso usa só o valor de mercado dos investimentos; bens e caixa entram apenas se o usuário marcar (RB-047).
- Taxa de retirada (padrão 4%) e retorno real (padrão 4% a.a.) são **premissas editáveis**, com rótulo (RB-048). O INSS não é calculado: o usuário informa o benefício esperado, se quiser.
- O aporte mensal necessário é arredondado **para cima** ao centavo.

## 11. Importação de extrato

- Só CSV, até 2 MB e 5.000 linhas; erros de leitura viram mensagens por linha.
- Fluxo em dois passos: pré-visualizar e confirmar. O registro da importação só existe depois de confirmado, na mesma transação dos lançamentos.
- **Possíveis duplicatas nunca são descartadas em silêncio** (RB-006): a pré-visualização marca linhas que já parecem existir, e reimportar o mesmo arquivo avisa (hash SHA-256 do arquivo).

## 12. Valores, datas e exportação

- `amount` é **sempre positivo**; a direção vem do tipo (receita/despesa) ou da origem/destino (transferência). Colunas `Numeric` com 2 casas e arredondamento explícito; `Decimal` no Python, nunca `float`.
- Datas sem horário (`YYYY-MM-DD`) são formatadas sem passar por `Date` no frontend, para não deslocar o fuso. A data padrão dos formulários usa o fuso local (`todayIso()`).
- No backend, "hoje" é a data do servidor (UTC). Entre 21h e 24h em Brasília, algo que vence "hoje" já aparece como atrasado. Corrigir exige o pacote `tzdata` na imagem.
- CSV exportado: UTF-8 com BOM, separador `;`, vírgula decimal. Células de **texto** que começam com `=`, `+`, `-`, `@`, tab ou CR ganham `'` na frente (proteção contra injeção de fórmula); números não.
