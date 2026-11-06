# Glossário

Termos do domínio como são usados no CashTrail. Entre parênteses, o nome no código.

| Termo | Significado |
|---|---|
| **Amortização** (`debt_amortizations`) | Pagamento extra que reduz o principal de uma dívida e regera as parcelas em aberto. |
| **Ativo** | O que a pessoa tem: caixa, bens e investimentos (pelo valor de mercado). |
| **Avaliação** (`asset_valuations`) | Valor de um bem numa data. O bem vale a última avaliação até a data consultada. |
| **Baixa** (`commitment_settlements`) | Registro do pagamento ou recebimento de um compromisso. Pode ser parcial. |
| **Bem** (`assets`) | Imóvel, veículo ou outro patrimônio físico. |
| **Caixa / conta de caixa** | Conta que é dinheiro disponível: corrente, poupança, carteira. Cartão, dívida e investimento não são caixa (`NON_CASH_TYPES`). |
| **Competência** | Regime em que o fato conta na data em que aconteceu (a compra), não quando o dinheiro saiu. Usado pelo DRE. |
| **Compromisso** (`commitments`) | Conta a pagar ou a receber, com vencimento. Vira lançamento na baixa. |
| **Contagem única** | Regra central: cada movimentação entra uma vez no resultado. Ver [regras](regras-de-negocio.md#1-contagem-única). |
| **Cotação** (`investment_quotes`) | Preço de um ativo numa data, com a fonte (brapi, manual ou o preço da operação). |
| **Custo médio** | Preço médio ponderado das compras de um ativo, incluindo taxas. Base para calcular o ganho na venda. |
| **DARF** | Guia de recolhimento do imposto sobre ganho em renda variável, paga no mês seguinte ao da venda. |
| **Dia apertado** | Dia do mês com saldo entre os 25% mais baixos, destacado no calendário. |
| **DRE** | Demonstrativo de resultado: receitas menos despesas do período, por grupo, em regime de competência. |
| **Encargos** | Parte da parcela de uma dívida que não é principal: juros, IOF, seguro, tarifas. É despesa. |
| **Fatura** | Soma das compras de um ciclo do cartão, identificada pela data de fechamento. Calculada, não gravada. |
| **Fechamento** | Dia em que o ciclo do cartão termina. Compras até esse dia, inclusive, entram na fatura que fecha. |
| **Fluxo de caixa** | Entradas e saídas de dinheiro por mês, realizadas e previstas, em regime de caixa. |
| **Grupo de DRE** (`dre_group`) | Linha do DRE a que uma categoria pertence (receitas, despesas fixas, financeiras etc.). |
| **Informe de rendimentos** (`tax_income_statements`) | Documento anual da fonte pagadora com bruto, INSS e IRRF. Digitado pelo usuário. |
| **Lançamento** (`transactions`) | Receita ou despesa realizada numa conta, com categoria. A entidade central do domínio. |
| **Marca fiscal** (`ir_kind`) | Classificação de uma categoria de despesa para o IRPF (saúde, educação, previdência). |
| **Passivo** | O que a pessoa deve: dívida dos cartões e saldo devedor das dívidas. |
| **Patrimônio líquido (PL)** | Ativos − passivos. |
| **Premissa** | Valor escolhido pelo usuário, não um fato (taxa de retirada, retorno real). A tela marca como tal. |
| **Previsto** | Valor esperado na data de vencimento (compromissos, faturas, recorrências), mesmo que já pago. |
| **Price / SAC** | Sistemas de amortização: Price tem parcelas iguais; SAC tem principal igual e parcelas decrescentes. |
| **Principal** | Valor emprestado, sem juros. Pagar principal é transferência, não despesa. |
| **Projetado** | Realizado + o que falta do previsto. |
| **Provento** | Dividendo, JCP ou rendimento recebido de um investimento. Receita financeira. |
| **Realizado** | Movimento com data até hoje. |
| **Recorrência** (`recurring_transactions`) | Regra que gera lançamentos ou compromissos periodicamente (semanal ou mensal). |
| **Saldo devedor** | Quanto falta pagar de principal numa dívida (−saldo da conta `loan`). |
| **Saldo inicial** (`opening_balance`) | Saldo da conta no começo do uso do app. |
| **Slice** | Pasta que reúne tudo de uma funcionalidade (rota, regra, dados, testes). Ver [arquitetura](../arquitetura/visao-geral.md#vertical-slices). |
| **Taxa de retirada** | Percentual do patrimônio retirado por ano na independência financeira (padrão 4%). |
| **Transferência** (`transfers`) | Dinheiro movido entre contas do próprio usuário. Não é receita nem despesa. |
| **Valores reais** | Valores em poder de compra de hoje, descontada a inflação. A simulação de independência usa só valores reais. |
