# CashTrail — Marco 15: Seguros e aposentadoria / independência financeira (desenho)

> Último marco do roadmap ([22](22-erp-pessoal-discovery.md), v4). Depende do patrimônio (Marco 12, [27](27-marco-12-patrimonio-e-balanco.md)), dos investimentos (Marco 13, [28](28-marco-13-investimentos.md)) e das contas a pagar e recorrências (Marco 8, [23](23-marco-8-contas-a-pagar-receber.md)). Segue o fluxo do projeto: **desenho e decisões antes de qualquer código**. Nada aqui foi implementado.

Legenda: **FATO** (verificado agora) · **FATO (secundário)** (blog/portal, não oficial) · **INFERÊNCIA** · **DESCONHECIDO**.

> **Aviso:** simulações de aposentadoria são **premissas, não previsões nem recomendação de investimento**. O sistema mostra as hipóteses usadas e cenários, nunca um número único como garantia.

## 1. Objetivo e critério de saída

**Objetivo:** (a) não perder prazo nem cobertura de seguro e ter o prêmio dentro do fluxo de caixa; (b) responder "**quanto preciso ter para parar de trabalhar e em quanto tempo chego lá**" a partir do patrimônio investido real.

**Critério de saída:**
1. Cada apólice mostra vigência, prêmio e renovação, e o prêmio **aparece nas contas a pagar e no fluxo de caixa** sem lançar duas vezes.
2. Há alerta de renovação nos próximos 30 dias e lista de **bens sem seguro**.
3. Com renda desejada, retorno real e taxa de retirada informados, o sistema calcula o **patrimônio-alvo**, o **progresso** e os **anos até chegar lá**, e a conta bate com uma conta manual.
4. A tela mostra **cenários** (taxa de retirada e retorno), não só o caso base.
5. Tudo em **poder de compra de hoje** (sem inflar valores com uma inflação inventada).

## 2. O que já existe (FATO — o código)

- **Recorrências** semanais e mensais, com opção de gerar **conta a pagar** (Marco 8); compromissos únicos e parcelados.
- **Patrimônio** e **valor de mercado dos investimentos** em qualquer data (Marcos 12 e 13); **bens** com avaliações.
- **DRE**, categorias com grupo e marca fiscal; **PGBL** já é marca de dedução no IRPF (Marco 14).
- Fonte de índices do Banco Central (IPCA série 433 verificada no Marco 13).

## 3. Pesquisa (2026-10-15)

| Tema | O que foi verificado | Fonte |
|---|---|---|
| **PGBL × VGBL** | PGBL: contribuição dedutível até 12% da renda tributável, imposto sobre o **total** resgatado. VGBL: sem dedução, imposto só sobre o **rendimento**. A escolha entre tabela progressiva e regressiva é feita na contratação ou no primeiro resgate | **FATO** — Receita e Ministério da Previdência (via busca) |
| **Tabela regressiva** | 35% caindo 5 pontos a cada 2 anos até 10% após 10 anos, **por contribuição**; a opção é **irretratável**. Progressiva: 15% retido na fonte e ajuste na declaração | **FATO** — mesmas fontes |
| **Regra dos 4%** | Origem americana (Trinity/Bengen, carteira em dólar). Para o Brasil, fontes divergem: **3% a 3,5%** (conservador, horizonte longo) a **5% a 6%** (juros reais altos); a taxa segura depende da carteira e do horizonte | **FATO (secundário)** — blogs e portais, **com interesse comercial**; números de Selic e IPCA variam entre eles |
| **Aposentadoria pelo INSS** | **Não pesquisado.** Regras (idade mínima, tempo de contribuição, cálculo do benefício) mudaram na reforma de 2019 e têm regras de transição | **DESCONHECIDO** |
| **Regras de seguros (SUSEP)** | **Não pesquisado.** O desenho só **cadastra** apólices e vencimentos; não interpreta cobertura nem sinistro | **DESCONHECIDO** |

**INFERÊNCIA:** como a taxa de retirada segura é controversa para o Brasil, o desenho **não fixa um número**: usa um padrão **conservador e editável** e mostra a sensibilidade.

## 4. Escopo proposto

**Dentro:**
- **Apólices**: tipo (vida, saúde, auto, residencial, viagem, outro), seguradora, nome, prêmio e periodicidade (mensal ou anual), início, **renovação**, valor de cobertura, bem coberto (opcional), conta e categoria do pagamento, ativa ou não.
- **Prêmio no fluxo**: mensal vira recorrência com conta a pagar; anual vira uma conta a pagar na renovação; **renovar** cria o próximo ciclo.
- **Alertas**: renovação em até 30 dias (dashboard) e **bens sem seguro**.
- **Plano de independência financeira**: idade atual, idade-alvo, renda mensal desejada (hoje), benefício público esperado (informado, opcional), retorno real esperado, taxa de retirada, aporte mensal.
- **Cálculo**: patrimônio-alvo, progresso com o **valor de mercado dos investimentos** (e, opcionalmente, bens líquidos), anos e idade estimada para atingir, aporte necessário para a idade-alvo, e tabela de **cenários**.
- **Contexto**: IPCA dos últimos 12 meses (Banco Central) para calibrar o retorno real.

**Fora:**
- Cálculo de benefício e regras do **INSS** e de regimes próprios (o usuário informa o valor esperado, se quiser).
- Tributação do resgate de PGBL/VGBL e escolha entre tabelas (só informativo).
- Renda de aluguel, herança, eventos futuros (cenários pontuais), simulação estocástica (Monte Carlo).
- Interpretação de cobertura, sinistro, comparação de seguradoras.
- E-mail e push de lembrete (só alerta na tela, na v1).

## 5. Requisitos propostos

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RF-068 | Cadastrar apólice (tipo, seguradora, prêmio, periodicidade, vigência, cobertura, bem opcional) | Valor > 0; tipos fixos; bem e conta do próprio usuário |
| RF-069 | Prêmio gera contas a pagar | Mensal: recorrência gerando conta a pagar; anual: conta a pagar na renovação; sem lançamento duplicado |
| RF-070 | Renovar apólice | Avança a vigência e cria o próximo prêmio, mantendo o histórico |
| RF-071 | Alertas de renovação e bens sem seguro | Renovação em ≤ 30 dias e lista de bens ativos sem apólice ativa |
| RF-072 | Plano de independência financeira | Campos validados; um plano por usuário |
| RF-073 | Patrimônio-alvo, progresso, tempo e aporte necessário | Bate com a fórmula e com um cálculo manual (testes de propriedade) |
| RF-074 | Cenários | Grade de taxa de retirada × retorno real; destaca o caso base |
| RF-075 | Resumo no dashboard | Próxima renovação e progresso de independência |

| ID | Regra de negócio |
|---|---|
| RB-044 | Prêmio é despesa **do período** (competência da cobrança), não custo da cobertura inteira; entra no DRE como despesa da categoria escolhida |
| RB-045 | Simulação em **valores reais**: renda desejada e patrimônio em poder de compra de hoje; retorno informado é **real** (acima da inflação) |
| RB-046 | Patrimônio-alvo = (renda desejada − benefício público esperado) × 12 ÷ taxa de retirada |
| RB-047 | Progresso usa só o **valor de mercado dos investimentos** por padrão; bens e caixa de emergência não entram a menos que o usuário os inclua |
| RB-048 | Taxa de retirada e retorno vêm do usuário, com padrão conservador e rótulo "premissa" |

## 6. Decisões

### DECISÃO 1 — Como o prêmio entra no fluxo

- **ALTERNATIVAS:** **(a)** a apólice cria a recorrência (mensal) ou a conta a pagar (anual) por meio dos serviços existentes; **(b)** só lembrete de data, sem integração; **(c)** o usuário lança tudo à mão.
- **EVIDÊNCIAS:** recorrências e contas a pagar já alimentam fluxo de caixa, DRE e alertas (Marcos 8 e 10); recorrência só tem frequência semanal e mensal.
- **TRADE-OFFS:** (a) mantém uma fonte de verdade e o fluxo futuro correto; custo: sincronizar a apólice com o que foi gerado (editar prêmio ou encerrar) e tratar o anual como conta única. (b) é fácil, mas o prêmio fica fora do planejamento. (c) é a situação de hoje.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Média-alta.

### DECISÃO 2 — Como simular a independência financeira

- **ALTERNATIVAS:** **(a)** em valores reais, com taxa de retirada e retorno real editáveis, padrão conservador, cenários e dados atuais do patrimônio; **(b)** projeção nominal com inflação e Selic projetadas; **(c)** simulação estocástica (Monte Carlo).
- **EVIDÊNCIAS:** seção 3: a taxa segura é controversa e dependente de premissa; projetar inflação e juros nominais inventa precisão que não existe.
- **TRADE-OFFS:** (a) é transparente, conferível à mão e não promete nada; custo: depende do usuário escolher bem o retorno real. (b) parece mais "completo" e é mais enganoso. (c) é o mais robusto, mas exige distribuição de retornos que eu não tenho fonte verificada.
- **RECOMENDAÇÃO:** **(a)**, com padrão de **4%** de retirada e **cenários de 3,5% e 5%**, e retorno real base de 4% a.a. editável (**premissas**, não fatos). **CONFIANÇA:** Alta para o método; baixa para qualquer valor padrão (por isso editável).

### DECISÃO 3 — INSS e previdência pública

- **ALTERNATIVAS:** **(a)** fora: o usuário informa, se quiser, o benefício mensal esperado (do extrato do Meu INSS); **(b)** calcular o benefício pelas regras da reforma.
- **EVIDÊNCIAS:** não verifiquei as regras; têm transição e cálculo próprio; um erro aqui distorce o plano inteiro.
- **TRADE-OFFS:** (a) é honesto e simples; custo: o plano ignora o INSS por padrão (conservador). (b) exige pesquisa oficial extensa e manutenção por mudança de lei.
- **RECOMENDAÇÃO:** **(a)**. **CONFIANÇA:** Alta.

### DECISÃO 4 — Escopo dos alertas

- **ALTERNATIVAS:** **(a)** alertas só na tela (dashboard) na v1; **(b)** também e-mail de renovação via serviço de e-mail do Marco 7.
- **TRADE-OFFS:** (a) não depende de infraestrutura; custo: só avisa quando ela abre o app. (b) avisa de verdade; custo: precisa do Azure Communication Services ligado (etapa de Azure adiada) e de um agendador por usuário.
- **RECOMENDAÇÃO:** **(a)** agora; (b) quando o e-mail de produção existir. **CONFIANÇA:** Alta.

## 7. Modelo de dados proposto

- `insurance_policies`: `id`, `user_id`, `kind` (String + CHECK: `life|health|auto|home|travel|other`), `insurer`, `name`, `premium_amount`, `premium_frequency` (`monthly|annual`), `coverage_amount` (opcional), `starts_on`, `renews_on`, `asset_id` (FK opcional, `SET NULL`), `payment_account_id`, `category_id`, `recurring_id` (FK opcional, `SET NULL`), `commitment_id` (opcional), `is_active`, `notes`.
- `retirement_plans` (um por usuário): `current_age`, `target_age`, `monthly_income_wanted`, `public_benefit_monthly` (opcional), `real_return_annual`, `withdrawal_rate`, `monthly_contribution`, `include_assets` (bool).
- Nada guardado sobre apólice além de metadados (**sem número de apólice nem documentos**).

**Slices:** `insurance` (depende de `recurring`, `commitments`, `assets`, `accounts`, `categories`) e `retirement` (depende de `reports/net_worth` ou `investments` para o patrimônio). Ninguém depende delas, exceto o dashboard.

## 8. Plano de implementação

1. Migração: `insurance_policies` e `retirement_plans` (up/down/up/check + teste de migração real).
2. Funções puras de aposentadoria (patrimônio-alvo, tempo, aporte necessário, cenários) com testes de propriedade e exemplos de manual.
3. Slice `insurance`: CRUD, geração do prêmio (recorrência/conta a pagar), renovar, alertas e bens sem seguro.
4. Slice `retirement`: plano, cálculo com o patrimônio investido real, cenários, IPCA de contexto (provedor externo atrás da interface, com falso nos testes).
5. Frontend: `/insurance`, `/retirement`, cartões no dashboard.
6. Verificação no navegador e documentação.

## 9. Riscos

| ID | Risco | Mitigação |
|---|---|---|
| R-15.1 | Usuário trata a simulação como previsão | Aviso fixo, premissas explícitas, cenários, valores reais |
| R-15.2 | Taxa de retirada padrão induz a erro (fontes divergem) | Padrão conservador editável + sensibilidade 3,5/4/5 visível |
| R-15.3 | Prêmio duplicado (recorrência e conta a pagar) | A apólice é a única origem; teste de que não há lançamento em dobro |
| R-15.4 | Apólice divergir da recorrência após edição | Editar a apólice atualiza a recorrência; encerrar desativa os dois |
| R-15.5 | Dado sensível de saúde/seguro | Só metadados; isolamento por usuário; sem número de apólice nem documentos |
| R-15.6 | Cálculo ignora benefício público e inflação futura | Declarado como premissa; INSS informado opcional; tudo em valores reais |

## 10. Perguntas para a Julia

1. **Decisão 1:** a apólice cria o prêmio no fluxo (recorrência ou conta a pagar) (recomendado)?
2. **Decisão 2:** simulação em valores reais, 4% de retirada com cenários de 3,5% e 5% (recomendado)?
3. **Decisão 3:** INSS fora, com benefício esperado informado por você, opcional (recomendado)?
4. **Decisão 4:** alertas só na tela por enquanto (recomendado)?
5. Que **seguros** você tem hoje (vida, saúde, auto, residencial, viagem)? E já tem **PGBL/VGBL**?

**STATUS:** decisões 1 a 4 aprovadas como recomendadas (2026-10-15). Perfil (seguros e PGBL/VGBL) não informado: nada foi presumido, o cadastro é livre.

**IMPLEMENTADO (2026-10-15):** backend (734 testes no total) e frontend (`/insurance`, `/retirement`, alerta de renovação no dashboard) verificados no navegador: apólice anual de R$ 2.400 virou **uma** conta a pagar, a Casa apareceu como bem sem apólice (o carro estava coberto), e o plano (35 → 55 anos, renda R$ 5.000, benefício R$ 1.000, retirada 4%, retorno real 4%) deu alvo de R$ 1.200.000, progresso de 25,0% com R$ 300.000 investidos e a grade de 9 cenários.

**Decisões ao codar:**
- Anual: o prêmio do ciclo anterior **não** muda quando o novo prêmio é informado na renovação (só o novo ciclo usa o valor novo). Mensal: a recorrência é atualizada.
- O aporte necessário é arredondado **para cima** ao centavo: o teste mostrou que arredondar normalmente podia faltar um mês.
- Encerrar a apólice desativa a recorrência (mensal) ou cancela a conta a pagar em aberto (anual).
- IPCA de 12 meses do Banco Central é só contexto, com cache do dia para o provedor real; falha da fonte não impede o plano.
- Progresso usa só o valor de mercado dos investimentos; bens entram apenas se você marcar.
- Alertas só na tela (e-mail depende do Azure Communication Services, adiado).
