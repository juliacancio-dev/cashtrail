# CashTrail — Descoberta: do controle financeiro ao ERP pessoal (FASE 22)

> **Gatilho:** em 2026-10-06 a Julia disse que quer "um ERP pessoal foda, tipo o do Bling e semelhantes". Isso muda o **escopo do produto**, não só a aparência. Nenhum código é escrito nesta fase; ela existe para que cada decisão seja defensável (ver [feedback do projeto](00-project-brief.md)).

Legenda: **FATO** (fonte citada) · **HIPÓTESE** (proposta minha) · **DESCONHECIDO** / **NÃO ENCONTRADO**.

## 1. O que a Julia respondeu (FATO — respostas diretas)

| Pergunta | Resposta |
|---|---|
| O que é "ERP pessoal"? | **Gestão end-to-end da vida financeira pessoal** (esclarecido pela Julia: *não* é vendas, cadastro de produtos ou estoque; a referência ao Bling é a **integração de ponta a ponta**, não os módulos de negócio). Não inclui documentos, agenda ou tarefas. |
| Módulos da primeira versão | **Contas a pagar e a receber**, **Fluxo de caixa e relatórios (DRE)**, **Investimentos e patrimônio** |
| Visual | **Ainda não sabe dizer** — quer ver exemplos pesquisados antes de decidir |
| Feedback da rodada de mockups (FASE 21) | Rejeitou as 4 direções como "genéricas, padrão de IA"; gostou de resumo evidente, gráfico em destaque e modo escuro; não gostou de laranja |

## 2. O que é um ERP "tipo Bling" (pesquisa)

**FATO** ([bling.com.br](https://www.bling.com.br/), [gestão financeira](https://www.bling.com.br/gestao-financeira)):
- Módulos: **financeiro** (contas a pagar e receber, fluxo de caixa, meios de pagamento), **estoque**, **vendas** (pedidos, NF-e, PDV), **logística**, **cadastros** (produtos, fornecedores), multiempresa.
- Relatórios financeiros: **fluxo de caixa, DRE e balancete financeiro**.
- **Conciliação bancária** importando extrato **OFX** e comparando com o que já foi lançado.
- Dashboard central chamado **"Meu Negócio"**; mais de 250 integrações.
- O financeiro é alimentado pelos outros módulos: cada venda gera a movimentação financeira sozinha.

**FATO** (comparativos: [Adrion](https://adrion.com.br/blog/tiny-bling-conta-azul-omie-comparativo-honesto-pme/), [Dinheiro da Minha Empresa](https://dinheirodaminhaempresa.com/comparativos/erp-conta-azul-omie-bling-tiny-2026/)): Bling é o "generalista" (fiscal + marketplaces); **Conta Azul** é o mais forte em **financeiro**; Omie sobe para PME média. Preços de entrada: Bling R$ 35/mês, Omie R$ 95, Conta Azul R$ 89, Tiny R$ 89.

**Lição estrutural (INFERÊNCIA):** o que define um ERP não é a aparência, é que **os módulos conversam entre si** (uma venda vira conta a receber, que vira fluxo de caixa, que entra no DRE). O CashTrail hoje tem lançamentos isolados; para ser um ERP precisa de **compromissos futuros** que se transformam em lançamentos realizados.

## 3. Estrutura de interface desses sistemas

**FATO** ([novos menus do Bling](https://ajuda.bling.com.br/hc/pt-br/articles/27625644954519-Novos-Menus-do-Bling-O-que-mudou-e-como-continuar-utilizando-o-sistema)): **menu principal lateral** com todos os módulos; nas telas de listagem, **filtros do lado esquerdo** (seleciona vários, clica em "Filtrar" e vê o resultado ao lado); **barra de busca** global; dashboard de resumo.

**NÃO ENCONTRADO:** cores, tipografia e capturas de tela do Bling, Omie e Conta Azul. Não consegui ver as interfaces reais daqui. **Preciso de prints** (ou de você me descrever o que gosta nelas).

**HIPÓTESE (a validar com você):** a categoria "ERP" é **estruturalmente diferente** do "app de finanças bonito" que você rejeitou. O app de finanças é visual e leve (cartões, gráficos grandes). O ERP é **denso e orientado a trabalho** (menu por módulos, tabelas com filtros, busca global, ações em lote). Isso pode ser justamente o "autêntico" que faltou nas quatro direções, mas é uma suposição.

## 4. Mapa: do ERP de negócio para a vida pessoal

| Módulo no Bling & cia | Equivalente pessoal | Já existe no CashTrail? | Dados/regras novos |
|---|---|---|---|
| Contas a pagar | **Compromissos a pagar** (faturas de cartão, aluguel, boletos, parcelas, impostos) | Parcial: só recorrentes simples | Vencimento, status (aberto/pago/vencido), parcelas, baixa que **gera o lançamento** |
| Contas a receber | **Valores a receber** (salário, aluguel recebido, reembolsos, freela) | Não | Mesmo mecanismo, direção oposta |
| Fluxo de caixa | **Projeção de caixa**: realizado + previsto por período | Não (só saldo atual) | Soma de lançamentos + compromissos futuros + recorrências |
| DRE | **Resultado do período** por categoria (receitas − despesas) | Quase: os dados existem, falta a visão | Plano de categorias com hierarquia (grupo → categoria) |
| Balancete / balanço | **Balanço patrimonial pessoal**: ativos − passivos = patrimônio líquido | Não | Bens, dívidas, saldos de contas |
| (financeiro do Bling) conciliação OFX | Conciliação do extrato | Parcial: importação de CSV (Marco 7); OFX ficou de fora | Já decidimos CSV-only |
| Cadastros (fornecedores) | **Favorecidos** (quem recebe/paga) | Não | Cadastro simples, opcional |
| Estoque, vendas, NF-e, logística, cadastro de produtos | — | — | **Fora do escopo** (confirmado pela Julia: é de negócio) |
| Investimentos | **Carteira**: posições, proventos, rentabilidade | Não | Ver seção 5 |

### 4.1 O ciclo financeiro "end to end" (o que "integrado" quer dizer aqui)

Um ERP é um sistema em que **um dado é lançado uma vez e alimenta todo o resto**. Para a vida financeira pessoal, o ciclo completo tem estas etapas (**HIPÓTESE**: a divisão é minha, para a Julia aprovar):

| Etapa do ciclo | O que responde | Estado no CashTrail |
|---|---|---|
| 1. **Planejar** | Quanto posso gastar? O que quero alcançar? | Existe: orçamentos e metas |
| 2. **Registrar** | O que entrou e saiu? | Existe: lançamentos, recorrentes, importação de CSV |
| 3. **Comprometer** | O que vou pagar e receber, e quando? | **Falta**: contas a pagar e a receber (Marco 8) |
| 4. **Controlar** | O extrato do banco bate com o que lancei? | Parcial: importação (sem tela de conciliação dedicada) |
| 5. **Analisar** | Como estou indo? Para onde vou? | **Falta**: fluxo de caixa projetado e DRE (Marco 9) |
| 6. **Acumular** | Quanto tenho e quanto devo? Como rendem meus investimentos? | **Falta**: patrimônio, balanço e investimentos (Marcos 10 e 11) |
| 7. **Cumprir e proteger** | Cartão de crédito e faturas, dívidas e financiamentos, imposto de renda, seguros | **Falta, e a Julia confirmou que entra** (as quatro áreas) |
| 8. **Longo prazo** | Aposentadoria / independência financeira | **Falta, e a Julia confirmou que entra** |

**O ponto de integração que faz disso um ERP:** o compromisso (etapa 3) vira lançamento realizado (etapa 2) ao ser pago, o lançamento alimenta o orçamento (1), o fluxo de caixa (5) e o DRE (5), e o saldo das contas e dos investimentos alimenta o balanço (6). Hoje cada tela é uma ilha; o trabalho dos próximos marcos é ligar essas peças.

**Conceito do balanço pessoal** (FATO, [Suno](https://www.suno.com.br/artigos/balanco-patrimonial-pessoal/), [Omie](https://www.omie.com.br/blog/balanco-patrimonial-e-dre-diferencas/)): ativo = passivo + patrimônio líquido; o **balanço** mostra a estrutura (o que tenho e devo), o **DRE** mostra o resultado (o que entrou e saiu).

## 5. Investimentos: de onde vêm os dados

**FATO** ([API do Banco Central — SGS](https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic)): gratuita, **sem autenticação**, séries como Selic (código 11); desde março/2025 exige filtro de datas e limita consulta a 10 anos. Serve para **índices** (Selic, CDI, IPCA) e para comparar rentabilidade.

**FATO** ([brapi.dev](https://brapi.dev/pricing)): plano gratuito com **15.000 requisições/mês**, atraso de **30 min**, **1 ativo por requisição**, histórico de **3 meses**, token não obrigatório para cotações básicas. Pagos a partir de R$ 99,99/mês (dividendos, FIIs detalhados, Tesouro vêm nos pagos).

**DESCONHECIDO:** termos de uso da brapi para uso pessoal/portfólio público; se a cobertura de Tesouro Direto e renda fixa no plano gratuito basta. **Precisa ser validado antes de depender dela.**

## 6. Decisões

### DECISÃO 1 — Evoluir o CashTrail ou começar outro projeto

- **ALTERNATIVAS:** (a) evoluir o CashTrail (mudar o escopo no brief); (b) projeto novo.
- **EVIDÊNCIAS:** auth multiusuário, contas, categorias, lançamentos, recorrência, importação, CI/CD e deploy já existem e foram desenhados em vertical slices, com `transactions` como núcleo que as demais slices consomem.
- **TRADE-OFFS:** (a) reaproveita tudo, mas exige atualizar o [brief](00-project-brief.md) e o [12-mvp.md](12-mvp.md) (hoje dizem "gestão financeira pessoal"). (b) joga fora o que funciona.
- **RECOMENDAÇÃO:** **(a)**, mantendo o nome e ampliando o escopo.
- **CONFIANÇA:** Alta.

### DECISÃO 2 — Ordem dos módulos (Marcos 8+)

- **RECOMENDAÇÃO**, pela ordem de dependência (versão revisada, com as áreas que a Julia confirmou):

  | Marco | Módulo | Depende de | Observação |
  |---|---|---|---|
  | **8** | Contas a pagar e a receber | lançamentos (existe) | Base de tudo: compromisso com vencimento; a baixa gera o lançamento |
  | **9** | Cartões de crédito e faturas | Marco 8 | A fatura é uma conta a pagar; parcelas de compra entram no fluxo futuro |
  | **10** | Fluxo de caixa e DRE | Marcos 8 e 9 | Visões calculadas (realizado + previsto; resultado por categoria). Quase não cria dado novo |
  | **11** | Dívidas e financiamentos | Marco 8 | Parcelas viram contas a pagar; saldo devedor alimenta o passivo |
  | **12** | Patrimônio e balanço pessoal | Marco 11 | Ativos (contas, bens) − passivos (dívidas) = patrimônio líquido |
  | **13** | Investimentos | Marco 12 | Carteira, proventos e cotações; fonte de dados externa |
  | **14** | Imposto de renda (IRPF) | Marcos 12 e 13 | Consolida rendimentos, bens e despesas dedutíveis do ano; **regras da Receita não verificadas** |
  | **15** | Seguros e aposentadoria / independência financeira | Marcos 12 e 13 | Apólices e vencimentos; projeção de longo prazo a partir do patrimônio e dos investimentos |

- **POR QUÊ:** cada marco entrega valor sozinho e usa os anteriores; os que dependem de fonte externa ou de regra legal (13 e 14) ficam no fim, depois que a base está de pé.
- **ATENÇÃO:** são **8 marcos novos**, contra 6 do MVP original, e as estimativas de esforço **ainda não foram feitas** (DESCONHECIDO; a [FASE 14](14-estimates.md) cobre só o MVP). Sugestão de cortes naturais para a Julia poder parar em um ponto estável: **v2 = Marcos 8–10** (financeiro operacional), **v3 = Marcos 11–12** (patrimônio), **v4 = Marcos 13–15** (investimentos, imposto, longo prazo).
- **CONFIANÇA:** Média-alta na ordem; baixa no tamanho total.

### DECISÃO 3 — Modelo contábil

- **ALTERNATIVAS:** (a) **partida simples** (cada lançamento é uma entrada ou saída, como hoje) com categorias hierárquicas; (b) **partidas dobradas** (todo lançamento tem débito e crédito, como contabilidade de verdade).
- **EVIDÊNCIAS:** os ERPs acima expõem fluxo de caixa, DRE e balancete sem exigir que o usuário entenda débito/crédito; o balanço pessoal se resolve com ativos e passivos cadastrados.
- **TRADE-OFFS:** (b) é mais correto e "profissional", mas multiplica a complexidade (todo lançamento muda, a UI de lançamento fica mais difícil) e o ganho para uso pessoal é pequeno. (a) mantém o que já existe e deixa DRE e fluxo de caixa como visões derivadas.
- **RECOMENDAÇÃO:** **(a)**; reavaliar (b) só se aparecer uma necessidade concreta.
- **CONFIANÇA:** Média.

### DECISÃO 4 — Dados de mercado para investimentos

- **ALTERNATIVAS:** (a) tudo manual (você digita o valor atual); (b) índices pelo Banco Central + cotações manuais; (c) brapi para cotações automáticas.
- **RECOMENDAÇÃO:** **(b)** na primeira versão do módulo; **(c)** só depois de validar os termos e a cobertura (seção 5).
- **POR QUÊ:** (b) usa só fonte oficial e gratuita, sem risco de depender de um terceiro cujos termos não verifiquei.
- **CONFIANÇA:** Média.

### DECISÃO 5 — Direção visual

- **RECOMENDAÇÃO:** descartar a categoria "app de finanças bonito" e explorar a **categoria ERP** (menu lateral por módulos, listagens densas com filtros, busca global), **mas só depois de você ver exemplos reais**. Como não consegui capturas do Bling/Omie/Conta Azul, o próximo passo é você me mandar prints ou me dizer o que quer manter.
- **CONFIANÇA:** Baixa (depende de evidência visual que ainda não tenho).

### DECISÃO 6 — Fechar o Marco 7 antes de começar o ERP?

- **ALTERNATIVAS:** (a) fechar e **publicar** o Marco 7 como "v1" antes de qualquer trabalho de ERP; (b) começar o Marco 8 já.
- **EVIDÊNCIAS:** o Marco 7 está no código, mas **não foi publicado**; faltam o e-mail real, a checagem de backup (R-009) e o extrato real do seu banco.
- **TRADE-OFFS:** (a) dá uma base estável e uma demo no ar (o objetivo de portfólio do brief), mas atrasa o ERP. (b) avança, porém acumula mais coisa sem deploy, o que aumenta o risco do próximo deploy.
- **RECOMENDAÇÃO:** **(a)**.
- **CONFIANÇA:** Alta.

## 7. Riscos novos

| Risco | Por quê | Mitigação |
|---|---|---|
| **Escopo grande** (8 marcos novos, 5 áreas financeiras a mais) | É o risco R-001 (abandono do projeto) em outra forma | Cortes em versões (v2, v3, v4), cada uma utilizável sozinha; estimar antes de começar |
| **Regras do IRPF e de seguros** | Não verifiquei as regras da Receita Federal nem formatos de declaração | Pesquisar fontes oficiais antes de desenhar o Marco 14 |
| Dependência de dados de mercado | Termos e cobertura da brapi não verificados | Começar só com BCB + entrada manual |
| Reescrever demais | Mudar o modelo contábil (partida dobrada) quebraria o que existe | Decisão 3 (partida simples) |
| **Restrição do brief** | Nenhuma sobreposição com o trabalho da Julia na Greystar | Qualquer módulo de imóveis/aluguéis precisa ser desenhado só a partir de uso pessoal |
| Visual decidido no escuro | A pesquisa de UI anterior olhou só apps de finanças | Pedir prints/referências antes da próxima rodada |

---

**APROVADO pela Julia em 2026-10-06:** ordem dos marcos e cortes v2/v3/v4 (decisão 2); **fechar e publicar o Marco 7 antes de começar o Marco 8** (decisão 6); evoluir o CashTrail em vez de projeto novo (decisão 1, por consequência). Ainda em aberto: decisões 3 e 4 (modelo contábil, dados de mercado) e a visual (5), que depende de prints de ERPs.

**STATUS:** Ainda não pronto.

**PENDÊNCIAS:**
1. Aprovar ou ajustar as decisões 1 a 4 e 6.
2. Enviar prints/referências de ERPs (Bling, Omie, Conta Azul ou o que você usa) para a decisão 5.
3. ~~Definir o que entra além dos 3 módulos~~ — **resolvido:** cartões e faturas, dívidas e financiamentos, IRPF, seguros e aposentadoria. Documentos, agenda e tarefas ficam **fora**.
4. Aprovar a ordem revisada dos marcos (decisão 2) e os cortes v2/v3/v4.
5. Atualizar o [brief](00-project-brief.md) e o [12-mvp.md](12-mvp.md) quando a decisão 1 for aprovada.
