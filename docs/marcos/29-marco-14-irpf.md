# CashTrail — Marco 14: Imposto de renda (IRPF) — desenho

> Sétimo marco da fase "ERP pessoal" ([22](22-erp-pessoal-discovery.md)); depende dos saldos e bens (Marco 12, [27](27-marco-12-patrimonio-e-balanco.md)) e dos investimentos (Marco 13, [28](28-marco-13-investimentos.md)). Segue o fluxo do projeto: **desenho e decisões antes de qualquer código**. Nada aqui foi implementado.

Legenda: **FATO** (fonte oficial lida agora) · **FATO (secundário)** (blog/portal de contabilidade, não oficial) · **INFERÊNCIA** (conclusão minha) · **DESCONHECIDO** (não verificado).

> **Aviso de responsabilidade:** o CashTrail **não é o programa da Receita, não transmite declaração e não substitui contador**. O objetivo é organizar os dados do ano na ordem em que a declaração pede e estimar o imposto, sempre mostrando a fonte e o ano das regras. Os números do programa oficial prevalecem.

## 1. Objetivo e critério de saída

**Objetivo:** ao fim do ano, abrir uma tela "IRPF do ano" que reúne **o que declarar** (rendimentos, deduções, bens e direitos, dívidas) e **o que pagar durante o ano** (ganho de capital em renda variável), com uma **estimativa do imposto** (declaração completa × simplificada), pronta para conferir e digitar no programa da Receita.

**Critério de saída:**
1. A tela do ano-calendário mostra bens e direitos **em 31/12** (contas, investimentos, bens, dívidas) e eles batem com o patrimônio do Marco 12 nessa data.
2. A estimativa do imposto bate com um cálculo manual feito com a tabela oficial do ano, nas duas modalidades, e indica a mais vantajosa.
3. A apuração mensal de renda variável responde "quanto de DARF pagar e até quando" e mantém o prejuízo a compensar.
4. Toda regra e valor mostrado traz **ano-calendário e fonte**; mudar de ano não exige mexer na lógica, só nos parâmetros.
5. Nenhum CPF de terceiros é guardado (minimização de dados sensíveis).

## 2. O que já existe no CashTrail (FATO — o código)

- Lançamentos com **categoria** (e `dre_group`), contas, transferências, bens com avaliação (`acquisition_value` opcional), investimentos com **custo médio, vendas e proventos** por operação, dívidas com saldo devedor.
- Saldo de contas e valor de bens/investimentos **em qualquer data** (Marco 12).
- **Não existe**: classificação fiscal dos rendimentos e despesas, dependentes, informes de rendimentos, nem apuração mensal de ganho de capital com limites de isenção.

## 3. Regras verificadas (pesquisa de 2026-10-15)

**Contexto de datas (INFERÊNCIA):** hoje é 15/10/2026. A declaração do **ano-calendário 2025** já foi entregue (prazo foi em 2026). A próxima é a do **ano-calendário 2026**, entregue em 2027, **sob as regras da Lei 15.270/2025**, que mudou a tributação a partir de 1º/1/2026.

| Tema | O que foi verificado | Fonte |
|---|---|---|
| **Tabela progressiva anual** (exercício 2027, ano-calendário 2026) | Até R$ 29.145,60 isento; 7,5% (parcela a deduzir R$ 2.185,92); 15% (R$ 4.729,91); 22,5% (R$ 8.105,85); 27,5% acima de R$ 55.976,16 (R$ 10.904,66) | **FATO** — [página oficial de tabelas da Receita](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026) |
| **Deduções do ano-calendário 2026** | Dependente R$ 2.275,08 por ano; educação, limite R$ 3.561,50 por pessoa; desconto simplificado até R$ 17.640,00 | **FATO** — mesma página |
| **Redutor da Lei 15.270/2025** (anual) | Base até R$ 60.000,00: redução de R$ 2.694,15 (imposto zero); de R$ 60.000,01 a R$ 88.200,00: R$ 8.429,73 − 0,095575 × base; zera em R$ 88.200,00 | **FATO** — mesma página |
| **Tabela e redutor mensais** (fonte pagadora) | Mensal até R$ 5.000,00: redução R$ 312,89; de R$ 5.000,01 a R$ 7.350,00: R$ 978,62 − 0,133145 × rendimento; dependente mensal R$ 189,59 | **FATO** — mesma página |
| **Saúde** | Despesas com saúde do contribuinte e dependentes dedutíveis **sem limite**, só a parte não reembolsada; profissionais como nutricionista e enfermeiro, em regra, não | **FATO** — [Receita, despesas dedutíveis](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/preenchimento/manual-mir/pagamentos-ou-doacoes/despesas-dedutiveis) (via busca) |
| **Previdência (PGBL)** | Dedutível até **12%** dos rendimentos tributáveis, condicionada a contribuir ao regime geral; **VGBL não é dedutível** | **FATO** — [Receita, previdência privada](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/perguntas-frequentes/imposto-de-renda/dirpf/deducoes/despesa-de-previdencia-privada) (via busca) |
| **Ações (renda variável)** | 15% sobre o ganho líquido; **isenção quando as vendas de ações no mês somam até R$ 20.000,00**; ganho = venda − custo, com corretagem e emolumentos somados à compra e subtraídos da venda; imposto até o **último dia útil do mês seguinte**; **DARF código 6015**; esses ganhos **não entram** na base do imposto da declaração anual | **FATO** — [Receita, cálculo e pagamento](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/calculo-e-pagamento-do-imposto) e [isenções](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes) (via busca) |
| **Day trade** | 20% e **sem** isenção de R$ 20 mil | **FATO** (Receita, via busca) |
| **FII** | 20% sobre o ganho, sem a isenção de R$ 20 mil; prejuízo de FII só compensa FII | **FATO (secundário)** |
| **Compensação de prejuízo** | Cada modalidade compensa a si mesma (swing × swing, day trade × day trade, FII × FII) | **FATO (secundário)** |
| **Obrigatoriedade** | Rendimentos tributáveis acima de R$ 35.584,00 (declaração de 2026, ano-calendário 2025) | **FATO** — IN da Receita 2026 (via busca); **o valor do ano-calendário 2026 não foi verificado** |

**DESCONHECIDO (precisa ser verificado antes de codar, com fonte oficial):**
- Tratamento de **ETF, BDR, cripto, ouro e fundos**: não vou apurar até confirmar.
- **IRRF "dedo-duro"** em operações de bolsa e valor mínimo de DARF (R$ 10,00 é o que lembro; **não verificado**).
- **Imposto mínimo de altas rendas (IRPFM)** e retenção de **dividendos acima de R$ 50 mil/mês por pessoa jurídica** (10%) aparecem em fontes secundárias; não são necessários para uma carteira pessoal pequena e ficam **fora**, com aviso.
- **Ficha de bens e direitos**: códigos e grupos da declaração e regras de "situação em 31/12" (custo de aquisição, não valor de mercado). Preciso do manual do programa do ano.
- Tabela e deduções do ano-calendário 2026 podem mudar por **IN/MP posterior**; a página oficial lida diz "a partir do exercício 2027".

## 4. O problema central: três regimes que não se misturam

**INFERÊNCIA (a partir das fontes acima):**
- **Declaração anual** (tabela progressiva): salário, aluguel, autônomo, e as deduções.
- **Tributação exclusiva/definitiva e apuração mensal**: ganho de capital em renda variável é pago por **DARF mensal**, fora da base da declaração; só se informa na declaração.
- **Isentos e não tributáveis**: informados, não tributados (ex.: vendas de ações até R$ 20 mil/mês, poupança).

O CashTrail precisa **separar** esses três, senão soma tudo numa base só e calcula o imposto errado.

## 5. Escopo proposto

**Dentro:**
- **Classificação fiscal** das categorias de receita e despesa (tributável, isento, exclusivo; dedução de saúde, educação, previdência PGBL).
- **Dependentes** (só quantidade e apelido, **sem CPF**).
- **Informes de rendimentos** digitados do documento oficial (fonte pagadora, rendimento bruto, INSS, IRRF, 13º): é a fonte exata do que a declaração usa.
- **Bens e direitos e dívidas em 31/12** a partir de contas, investimentos (custo), bens (valor de aquisição) e dívidas.
- **Estimativa do imposto**: completa × simplificada, com a tabela do ano, redutor da Lei 15.270 e IRRF já retido.
- **Renda variável**: apuração mensal de ações (swing) e FIIs, isenção de R$ 20 mil, compensação de prejuízo e valor/prazo do DARF.
- **Exportação CSV** do dossiê para conferência (mesmas proteções do Marco 10).

**Fora:**
- Transmitir ou importar declaração, e conexão com e-CAC/gov.br.
- Day trade, ETF, BDR, cripto, ouro, opções e fundos (ficam como "não apurado", com aviso).
- Atividade rural, exterior, ganho de capital em imóvel e carnê-leão.
- Dividendos com retenção de 10% e IRPFM (Lei 15.270).
- Livro caixa, doações e deduções incentivadas.
- Conselho tributário: não é aconselhamento fiscal.

## 6. Requisitos propostos

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RF-059 | Tag fiscal em categorias (tipo de rendimento ou dedução) | Valores fixos validados; categoria sem tag aparece "não classificada" com contagem |
| RF-060 | Cadastro de dependentes (apelido, sem CPF) | Quantidade alimenta a dedução do ano; sem dado sensível |
| RF-061 | Informes de rendimentos do ano | Fonte pagadora, bruto, INSS, IRRF, 13º; soma por ano |
| RF-062 | Bens, direitos e dívidas em 31/12 | Conta/investimento/bem/dívida na data; bate com o patrimônio da data (exceto valor de mercado × custo, explicado na tela) |
| RF-063 | Estimativa de imposto anual | Completa × simplificada, tabela e redutor do ano, imposto a pagar ou restituir |
| RF-064 | Apuração mensal de renda variável | Vendas, ganho líquido, isenção, prejuízo acumulado, imposto e vencimento do DARF por mês |
| RF-065 | Parâmetros fiscais por ano-calendário, com fonte e data | Nada de valor fiscal fixo no código de regra |
| RF-066 | Exportar o dossiê (CSV) | Mesma proteção contra injeção de fórmula do Marco 10 |
| RF-067 | Aviso de limites | Toda tela de IRPF mostra ano, fonte e "não substitui o programa da Receita" |

| ID | Regra de negócio |
|---|---|
| RB-038 | Ganho de capital de renda variável **não** entra na base da declaração anual (regime próprio) |
| RB-039 | Venda de ações até R$ 20.000/mês é isenta **no mês**; ultrapassou, todo o ganho do mês é tributável |
| RB-040 | Prejuízo só compensa a mesma modalidade; fica acumulado entre meses |
| RB-041 | Bens e direitos usam **custo**, não valor de mercado |
| RB-042 | Parâmetros fiscais (tabela, limites, alíquotas) vivem em dados versionados por ano-calendário |
| RB-043 | Nenhum CPF/CNPJ de terceiro é armazenado |

## 7. Decisões

### DECISÃO 1 — Escopo do produto

- **ALTERNATIVAS:** **(a)** apoio à declaração: dossiê anual + estimativa + apuração mensal de renda variável, sem transmitir; **(b)** só relatório/CSV do que existe; **(c)** gerar o arquivo da declaração (`.DEC`) ou integrar com a Receita.
- **EVIDÊNCIAS:** a Receita não tem API pública de declaração para terceiros que eu tenha verificado; o programa oficial é o que valida; as regras mudaram em 2026 (Lei 15.270).
- **TRADE-OFFS:** (a) entrega o valor real (saber o que declarar e quanto pagar mensalmente) com risco contido; custo: a estimativa precisa estar certa e sempre avisar que é estimativa. (b) é barato, mas não responde "quanto pagar". (c) assume risco legal e dependência de formato proprietário, sem fonte verificada.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Alta.

### DECISÃO 2 — De onde vêm os dados fiscais

- **ALTERNATIVAS:** **(a)** tag fiscal nas categorias + informes de rendimentos digitados + dependentes por quantidade; **(b)** inferir tudo dos lançamentos; **(c)** tag por lançamento.
- **EVIDÊNCIAS:** o salário que cai na conta é **líquido**: bruto, INSS e IRRF só existem no informe oficial. O DRE já usa `dre_group` por categoria, então o padrão existe.
- **TRADE-OFFS:** (a) combina o que o sistema sabe (despesas de saúde, educação, bens, investimentos) com o que só o documento oficial tem; custo: o usuário digita poucos campos por ano. (b) erra o bruto e o IRRF. (c) é preciso demais para uso pessoal e vira trabalho manual.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Alta.

### DECISÃO 3 — Onde ficam as tabelas e limites fiscais

- **ALTERNATIVAS:** **(a)** dados versionados por ano-calendário (arquivo no repositório e/ou tabela), com fonte e data, carregados pela lógica; **(b)** constantes no código; **(c)** buscar de uma fonte online a cada uso.
- **EVIDÊNCIAS:** a Receita publica a tabela por exercício; as regras de 2026 mudaram no meio do ano; não há API oficial verificada de tabelas.
- **TRADE-OFFS:** (a) troca de ano sem mexer em regra e com teste por ano; custo: eu preciso atualizar os parâmetros todo ano, **com fonte oficial** (e isso vira checklist). (b) mistura dado volátil com lógica. (c) depende de fonte não verificada e falha silenciosa.
- **RECOMENDAÇÃO:** **(a)**, com teste que falha se o ano pedido não tiver parâmetros. **CONFIANÇA:** Alta.

### DECISÃO 4 — Quanto de renda variável apurar na v1

- **ALTERNATIVAS:** **(a)** ações (swing) e FIIs, com isenção de R$ 20 mil, compensação e DARF; ETF/BDR/cripto/day trade como "não apurado" com aviso; **(b)** tudo, inclusive day trade, ETF e cripto; **(c)** nada de renda variável.
- **EVIDÊNCIAS:** seção 3: ação e FII estão confirmados na Receita/secundário; ETF, BDR, cripto e IRRF de day trade não foram verificados; o modelo de operações guarda **data**, não horário, então day trade só pode ser **sinalizado** (compra e venda no mesmo dia), não apurado com precisão.
- **TRADE-OFFS:** (a) cobre o que uma carteira pessoal tem e o que está verificado, com aviso nos casos não cobertos; custo: usuário com ETF/cripto ainda calcula à mão. (b) afirma regras não verificadas, risco de imposto errado. (c) deixa o maior ganho de utilidade (DARF mensal) de fora.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Média-alta (FII e compensação são de fonte secundária; verifico na Receita antes de codar).

## 8. Modelo de dados proposto

- `categories.ir_kind` (String + CHECK, nulo = não classificada): `taxable_income`, `exempt_income`, `exclusive_income`, `deduction_health`, `deduction_education`, `deduction_pension`, `not_relevant`.
- `tax_dependents`: `id`, `user_id`, `nickname`, `is_active`. **Sem CPF** (RB-043).
- `tax_income_statements` (informes): `year`, `payer_name`, `gross_income`, `thirteenth`, `social_security`, `withheld_tax`, `note`.
- `tax_parameters` por ano-calendário (arquivo versionado carregado pelo serviço; **não** é tabela editável pelo usuário): faixas, redutor, dependente, limite de educação, limite do simplificado, limite de isenção de ações, alíquotas, fonte e data de consulta.
- `tax_loss_carryforward` **derivado** (não guardado): prejuízo acumulado calculado da série de meses a partir das operações (Marco 13).
- Nenhuma mudança em lançamentos, contas ou investimentos além da tag da categoria.

**Slice:** nova `tax` (informes, dependentes, parâmetros, estimativa, apuração). Depende só do `service` público de `accounts`, `categories`, `transactions`, `assets`, `debts`, `investments`. Ninguém depende de `tax`.

## 9. Plano de implementação

1. **Verificação oficial** pendente: ETF/BDR, IRRF, DARF mínimo e códigos de bens e direitos (anotar fonte no doc).
2. Migração: `ir_kind`, dependentes, informes (+ teste de migração real).
3. Parâmetros por ano com teste; funções puras do imposto (tabela, redutor, completa × simplificada) com testes de propriedade e exemplos oficiais.
4. Apuração mensal de renda variável (funções puras): isenção, compensação, DARF; testes de propriedade.
5. Dossiê do ano: rendimentos por regime, deduções, bens e direitos em 31/12, dívidas.
6. API e CSV; frontend (`/tax`): classificação, informes, dependentes, estimativa, renda variável mensal, bens e direitos.
7. Verificação no navegador e documentação.

## 10. Riscos

| ID | Risco | Mitigação |
|---|---|---|
| R-14.1 | **Regra fiscal errada ou desatualizada** gera estimativa errada | Parâmetros por ano com fonte e data; "estimativa, não substitui o programa"; testes contra os exemplos da Receita; só apurar o que foi verificado |
| R-14.2 | Lei muda no meio do ano (já mudou em 2026) | Parâmetros versionados; checklist anual de atualização; aviso quando o ano não tem parâmetro |
| R-14.3 | Dados fiscais sensíveis (renda, bens, dependentes) | Mesmo isolamento por usuário das demais slices; sem CPF; sem log de valores; CSV com proteção contra fórmula |
| R-14.4 | Usuário confia na estimativa e paga a menos | Texto explícito em toda tela; mostrar premissas e o que ficou de fora (day trade, ETF, cripto...) |
| R-14.5 | Custo de aquisição incompleto (bem sem valor de compra; investimento sem histórico) | Aviso por item "sem custo informado" e exclusão do total confiável |
| R-14.6 | Bens e direitos em 31/12 divergem do patrimônio de mercado | A tela explica: IR usa custo, patrimônio usa valor de mercado |

## 11. Perguntas para a Julia

1. **Decisão 1:** apoio à declaração (dossiê + estimativa + DARF mensal), sem transmitir (recomendado)?
2. **Decisão 2:** tag fiscal nas categorias + informes digitados + dependentes por quantidade, sem CPF (recomendado)?
3. **Decisão 3:** tabelas e limites em dados versionados por ano, atualizados com fonte oficial (recomendado)?
4. **Decisão 4:** renda variável só ações (swing) e FIIs na v1, com aviso para o resto (recomendado)?
5. **Seu perfil:** hoje você tem salário CLT? Tem dependentes? Gasta com saúde, educação ou previdência privada (PGBL)? Vende ações ou FIIs? Tem ETF, BDR ou cripto? Isso define o que priorizo.
6. **Ano-alvo:** concorda em mirar o **ano-calendário 2026** (declaração de 2027, sob a Lei 15.270)?

**STATUS:** decisões 1 a 4 aprovadas como recomendadas (2026-10-15). Perfil informado: salário CLT (com contrato, benefícios VR/VT e bônus), deduções de **saúde e educação** (sem dependentes nem PGBL), investimentos em **ações e renda fixa/Tesouro**. Ano-alvo: ano-calendário 2026.

**IMPLEMENTADO (2026-10-15):** backend (681 testes no total) e frontend (`/tax`, marca fiscal nas categorias) verificados no navegador: salário bruto R$ 100.000, INSS R$ 8.000, IRRF R$ 12.000, saúde R$ 4.000 e venda de ações de R$ 30.000 deram simplificada com imposto de R$ 11.744,34 (a restituir R$ 255,66), completa de R$ 13.295,34 (conferidas à mão contra a tabela oficial) e DARF de março de R$ 1.498,50 com vencimento em 30/04.

**Verificado agora para o seu perfil (pesquisa de 2026-10-15):**
- Ações: 15%, isenção de vendas até R$ 20 mil/mês, DARF 6015, prazo no último dia útil do mês seguinte e IRRF de 0,005% sobre a venda: **oficial**.
- VR/VA: alimentação fornecida pelo empregador é rendimento isento (fonte: Solução de Consulta da Receita, via notícia); **em dinheiro, para o setor privado, é tributável**. VT: fonte antiga e secundária.
- PLR: **fontes divergem** na faixa isenta (R$ 7.640,80 × R$ 8.214,40) e na base legal; **não calculado**.
- Renda fixa: tabela regressiva de 22,5% a 15% (Receita), LCI/LCA/poupança isentos; o banco retém na fonte.

**Decisões ao codar:**
- O sistema **não recalcula** salário, 13º, PLR nem renda fixa: usa os valores do informe de rendimentos digitado, que é o documento que a declaração usa. 13º, PLR e rendimento financeiro ficam fora da base do ajuste anual e seu imposto retido não compensa.
- Dependentes: só a quantidade, sem CPF (RB-043). Marcas fiscais só para **despesas** (saúde, educação, previdência).
- Day trade (compra e venda no mesmo dia) e classes sem regra verificada (ETF, BDR, cripto, fundos) são **sinalizados e não apurados**.
- Redutor da Lei 15.270 usa os rendimentos tributáveis como base e é zero em R$ 88.200 (a fórmula dá centavos no teto por arredondamento).
- Parâmetros em `tax/parameters/2026.json` com fonte, data da consulta e lista do que não foi verificado; ano sem arquivo é erro explícito (422).
- **Atualização anual:** ao virar o ano, criar o JSON do novo ano a partir da página oficial de tabelas da Receita e rodar os testes de cálculo.

**Pendências de verificação oficial (aparecem na tela):** 20% do desconto simplificado, base do redutor, 20% de FII e compensação por modalidade, valor mínimo do DARF e aplicação do IRRF a FIIs.
