# Marco 17 — Acabamento: Resumo do mês e telas densas no estilo calmo

> Status: **APROVADO pela Julia em 2026-11-04** (decisões 1 a 7 como recomendadas; decisão 8, a navegação, depois
> de 5 rodadas de protótipo). Etapa 1 feita.
> Protótipos: telas https://claude.ai/artifact/Gt9MK8wu4X9jDbFVUDoykw · cápsula e gaveta
> https://claude.ai/artifact/Q8DKAi4wjzztyztvMUfHHS
> Continua o Marco 16 (doc 32), que trocou as cores e o menu mas deixou o miolo das telas como estava.
> O colchão (doc 32, backlog) fica para o Marco 18.

## 1. Objetivo

Corrigir os defeitos visíveis que sobraram e trazer as 4 telas mais usadas para o mesmo estilo do
calendário: um número principal, uma frase, uma lista limpa e as ações aparecendo só quando pedidas.

## 2. Diagnóstico (lido no código em 2026-11-04)

| # | Achado | Onde | Gravidade |
|---|---|---|---|
| A1 | "Evolução de saldo" repete datas e tem pontos soltos: o backend gera **um ponto por lançamento**, não por dia. Dois lançamentos no dia 3 viram dois "03". | `backend/src/features/dashboard/service.py:44` | defeito |
| A2 | O mesmo gráfico começa em zero e soma só o mês: é o **resultado acumulado**, não o saldo da conta. O nome "saldo" engana, e o calendário já mostra o saldo real dia a dia. | idem | defeito de conceito |
| A3 | Título "Dashboard" e aba "Resumo do mês". | `app/(app)/dashboard/page.tsx:80` | visual |
| A4 | Subtítulo com datas cruas (`2026-11-01 a 2026-11-30`); a lista de lançamentos também mostra `2026-11-04`. | `dashboard/page.tsx:83`, `transaction-list.tsx:40` | visual |
| A5 | **Data padrão dos formulários usa UTC** (`toISOString`). No Brasil, depois das 21h o formulário já sugere o dia seguinte; no orçamento, no último dia do mês depois das 21h, sugere o mês seguinte. | `transaction-form.tsx:47`, `contribution-form.tsx:42`, `recurring-form.tsx:50`, `budget-form.tsx:21` | defeito |
| A6 | 7 telas mostram o e-mail da pessoa como subtítulo, sem função. | accounts, categories, budgets, goals, recurring, commitments, transactions | visual |
| A7 | Lançamentos carrega **todos os lançamentos de sempre**, sem filtro de período, cada um num cartão. Vai ficar lento e longo com o extrato real importado. | `transactions/page.tsx:33` | desempenho + visual |
| A8 | Compromissos: cada conta é um cartão com 3 ou 4 botões sempre visíveis; 5 filtros sempre abertos; 3 cartões de resumo e mais uma frase de totais. | `commitments/page.tsx`, `commitment-list.tsx` | poluído |
| A9 | Cartões: cada fatura (passadas e futuras) é uma caixa com botões; tudo aberto por padrão. | `card-panel.tsx`, `invoice-row.tsx` | poluído |

## 3. Decisões

### Decisão 1 — O que fazer com "Evolução de saldo"

**ALTERNATIVAS**
- (a) **Tirar o gráfico** do Resumo do mês e pôr no lugar uma linha "Ver o saldo dia a dia no calendário".
- (b) Consertar: um ponto por dia, com o nome certo, "Resultado acumulado do mês".
- (c) Consertar e trocar pelo saldo real das contas (abertura + movimentos).

**TRADE-OFFS:** (a) tira um defeito e uma repetição de uma vez, e a tela fica mais calma. (b) mantém um gráfico que
pouca gente lê bem ("acumulado" é abstrato). (c) duplica a linha do calendário.

**RECOMENDAÇÃO:** (a). O campo `balance_evolution` da API fica, agregado por dia (correção pequena e testada), para não
quebrar quem já chama; a tela só deixa de usar. **CONFIANÇA:** média-alta.

### Decisão 2 — Layout do Resumo do mês

**RECOMENDAÇÃO**
- Título "Resumo de novembro" e navegação ‹ mês › igual à do calendário (hoje a tela só mostra o mês atual).
- Topo no estilo K: **um número** (quanto sobrou no mês, em mono grande) e **uma frase**:
  "Entraram R$ X e saíram R$ Y em novembro." Sem os 3 cartões.
- **Atenção** numa lista só, em vez de 4 caixas (contas vencendo, faturas, dívidas, seguros): uma linha por aviso,
  cada uma levando à tela certa; some quando não há aviso.
- Patrimônio líquido vira uma linha discreta ("Patrimônio: R$ X, + R$ Y no mês").
- "Gasto por categoria" fica (barras horizontais, uma cor, já conferido na etapa 5 do Marco 16), ordenado do maior
  para o menor.

**ALTERNATIVAS:** manter os cartões e só trocar o título e as datas (mínimo); ou levar tudo isso para o calendário e
apagar o Resumo (perde a visão por categoria). **CONFIANÇA:** média — quero que você veja no protótipo (decisão 6).

### Decisão 3 — Lançamentos

**RECOMENDAÇÃO**
- Um mês por vez, com ‹ mês › (a API já aceita `start_date`/`end_date`): resolve A7.
- Lista **agrupada por dia** ("terça, 4 de novembro" e o total do dia à direita), linhas finas em vez de cartões:
  descrição; categoria · conta em tom apagado; valor em mono com sinal e cor.
- Formulário escondido atrás de "Novo lançamento" (como em Compromissos).
- Topo: entrou / saiu no mês numa frase só.

**ALTERNATIVAS:** tabela com colunas (mais densa, pior no celular); manter cartões só com datas formatadas (mínimo).
**CONFIANÇA:** alta.

### Decisão 4 — Compromissos

**RECOMENDAÇÃO**
- Os 3 cartões de resumo e a frase de totais viram **uma frase**: "A pagar R$ X (2 vencidas) · a receber R$ Y".
- Filtros: fica visível só o seletor Todas / A pagar / A receber; situação, categoria e datas vão para um botão
  "Filtros" que abre o painel (e mostra quantos filtros estão ativos).
- Lista agrupada por vencimento ("Vencidas", "Esta semana", "Mais tarde"), em linhas finas.
- Na linha fica **só a ação principal** (Pagar / Receber). Editar, baixas e cancelar aparecem ao abrir a linha.

**ALTERNATIVAS:** menu "⋯" por linha (menos descobrível para quem usa teclado; mais um componente); manter os botões
e só trocar cartão por linha. **CONFIANÇA:** média-alta.

### Decisão 5 — Cartões

**RECOMENDAÇÃO**
- Por cartão: nome, "fecha dia X · vence dia Y", dívida em mono e a barra de limite fina.
- Só a **fatura atual** (aberta ou fechada a pagar) aparece aberta, com "Pagar fatura". As outras viram uma lista
  recolhida "Faturas anteriores e futuras", uma linha cada (mês, valor, situação).
- "Nova compra" continua visível; "Editar cartão" vai para dentro de um link discreto.

**CONFIANÇA:** média-alta.

### Decisão 6 — Ver antes de construir

**RECOMENDAÇÃO:** protótipo estático das 4 telas (claro e escuro), no mesmo formato das rodadas do Marco 16, antes
de qualquer código das etapas 2 a 5. A etapa 1 (defeitos) não depende do protótipo e pode começar já.

### Decisão 7 — Correções miúdas (sem alternativa real)

- A5: trocar `toISOString()` por `todayIso()` / `currentMonthIso()`, que já existem em `lib/format.ts` e usam o
  fuso local.
- A4: todas as datas na tela via `formatDate`.
- A6: tirar o e-mail das 7 telas (ele já está implícito no "Sair").

### Decisão 8 — Navegação: cápsula Tinta + âmbar com gaveta no logo

**APROVADA pela Julia em 2026-11-04**, depois de 5 rodadas de protótipo no mesmo dia (o protótipo das 4 telas
aprovado mostrou que o cabeçalho do Marco 16 não agradava: "tudo da mesma cor").

**Como fica**
- **Cápsula flutuante** no topo (substitui o cabeçalho de duas linhas do Marco 16): logo, os 6 módulos como pílulas,
  tema e Sair. O módulo atual é uma pílula âmbar. Embaixo da cápsula, fora dela, as telas do módulo com a atual
  sublinhada: é o **acesso rápido** (um clique para trocar de módulo ou de tela).
- **Logo "C" é o botão do menu** (`aria-label="Abrir menu"`, `aria-expanded`): ao lado do "C", três tracinhos
  de tamanhos diferentes que ficam iguais no hover e viram X com o menu aberto; dica "Menu" no hover; um anel
  âmbar pisca duas vezes ao carregar, só como aviso.
- **Gaveta** (animação escolhida, entre "nasce do logo" e "gaveta"): desliza da esquerda em ~300 ms, itens em
  cascata, fundo escurecido; fecha com Esc, clique fora ou ao escolher uma tela. Sem movimento com
  `prefers-reduced-motion`.
- **Conteúdo da gaveta:** busca "Ir para uma tela" (tecla `/` abre direto nela; Enter vai para a primeira
  encontrada), as 20 telas agrupadas por módulo com ícone, **cabeçalho de cada seção numa faixa mais escura** que
  as telas clicáveis (pedido dela: "de uma cor só não dá pra entender que são seções"), tela atual marcada, tema e
  Sair no pé.
- **Celular:** a cápsula mostra só o logo, o módulo atual e o tema; a gaveta ocupa ~86% da largura.

**Cores (paleta "A · Tinta + âmbar")**

| Elemento | Claro | Escuro |
|---|---|---|
| Fundo da cápsula e da gaveta | `#18181b` (o preto dos botões, `--foreground`) | `#26262b` + fio de borda `#34343a` (o `#18181b` some no fundo `#111113`) |
| Texto / texto apagado | `#f4f4f5` / `#a1a1aa` | igual |
| Pílula do módulo atual e quadrado do "C" | `#f2b53a` com texto `#18181b` (~10:1) | igual |
| Cabeçalho de seção na gaveta | `#3a3a41`, texto branco | `#3d3d44` |
| Busca / hover | `#232326` / `#2e2e33` | `#1c1c20` / `#34343a` |
| Sublinhado da aba atual | `--accent-money` | `--accent-money` |

Forma leve: sem borda colorida, sombra `0 2px 8px` com 8% de opacidade, raio 14 px (o mesmo dos quadros).

**ALTERNATIVAS vistas e descartadas:** 4 estruturas na cor do fundo (rodada 1); 6 faixas coloridas (rodada 2:
escolheu Areia); 7 estruturas em Areia (rodada 3: escolheu cápsula + lateral); 8 paletas para a cápsula
(rodada 4: Areia descartada, escolheu "Tinta + ardósia A"); ardósia aplicada nas 4 telas "não casou" (rodada 5).
**Por que não casou** (diagnóstico confirmado por uma segunda opinião que ela trouxe): azul frio sobre app quente;
o azul já significa "informação" nos chips e no gráfico; três cores disputando o papel de "ativo"; a barra mais
forte que o número principal. Também vistas: "aba preta" (âmbar só no logo e na pílula) e "clara" (cartão +
pílula preta, perde personalidade).

**TRADE-OFF:** o âmbar passa a ser marca **e** destaque de dinheiro. Ela aceitou; se cansar, a variante "aba
preta" é a saída sem refazer nada. **Regra:** azul fica só para informação e gráficos.

## 4. Plano (uma branch por etapa, merge `--no-ff` no fim do marco)

| Etapa | O que | Verificação |
|---|---|---|
| 1. Defeitos | A1 (backend, um ponto por dia + teste), A3, A4, A5, A6 | `pytest` da slice `dashboard`; teste do fuso no navegador com `timezoneId` em America/Sao_Paulo às 22h; `lint`/`tsc`/`build` |
| 2. Navegação | Decisão 8: cápsula, gaveta no logo, busca, celular; substitui o `AppHeader` do Marco 16 nas 20 telas | roteiro: as 20 telas pela cápsula, pelas abas e pela gaveta; busca e `/`; Esc e foco voltando ao logo; celular sem rolagem horizontal; contraste medido nos dois temas; `prefers-reduced-motion` |
| 3. Resumo do mês | Decisões 1 e 2 | roteiro de navegador nos dois temas, números conferidos com a API |
| 4. Lançamentos | Decisão 3 | roteiro: troca de mês, agrupamento por dia, criar lançamento, celular sem rolagem horizontal |
| 5. Compromissos | Decisão 4 | roteiro: filtros, agrupamento, pagar, editar, desfazer baixa (repete o e2e do Marco 8) |
| 6. Cartões | Decisão 5 | roteiro: fatura atual aberta, pagar fatura, mover compra (repete o e2e do Marco 9) |

A navegação vem antes das telas porque todas ficam embaixo dela.

**Estimativa (por analogia com o Marco 16, não medida):** 18 a 30 horas; as etapas 2 e 5 são as maiores.

## 5. Riscos

| Risco | Mitigação |
|---|---|
| Esconder ações deixa algo difícil de achar | Ação principal sempre visível; o resto a um clique; roteiros dos Marcos 8 e 9 continuam passando |
| Mudar a forma da lista quebra os e2e antigos | Rodar todos os roteiros de `scripts/e2e` no fim de cada etapa |
| Tirar "Evolução de saldo" fazer falta | O calendário cobre; se sentir falta, volta como (b) |

## 5a. Fora do escopo

- Colchão (Marco 18).
- Previsão com gastos variáveis (precisa de discovery própria).
- As outras 16 telas no estilo calmo (cada uma vira um passo depois, se fizer sentido).

## STATUS

**Etapa 1 (defeitos) — feita em 2026-11-04, branch `marco-17-etapa-1-defeitos`.**
- A1: `dashboard/service.py` guarda o acumulado por dia (último lançamento do dia); teste novo
  `test_dashboard_balance_evolution_has_one_point_per_day`.
- A3/A4: título "Resumo do mês" com período `dd/mm/aaaa`; datas formatadas também em Lançamentos, Recorrências,
  Metas (prazo) e Orçamentos (`nov/2026`) — as três últimas apareceram na busca por datas cruas.
- A5: `todayIso()` / `currentMonthIso()` nos 4 formulários.
- A6: e-mail removido das 7 telas.
- Verificado: `pytest` de `dashboard` e `reports` (100 ok), `lint`, `tsc`, `build`;
  `scripts/e2e/e2e-m17-defeitos.mjs` 13/13 com o relógio do navegador às 22h30 do último dia do mês em São Paulo
  (UTC já no mês seguinte); regressão `e2e-m16-menu` e `e2e-m16-calendario` ok.

**Etapa 2 (navegação) — feita em 2026-11-04, branch `marco-17-etapa-2-navegacao`.**
- `globals.css`: tokens `--nav*` nos dois temas (tabela da decisão 8) e o anel `nav-ping` (desligado com
  `prefers-reduced-motion`).
- `app-shell/app-header.tsx`: cápsula com o logo-botão (três tracinhos que viram X, dica "Menu"), pílulas dos
  módulos (no celular só a atual), tema e Sair; linha de abas embaixo com sublinhado `accent-money`; atalho `/`
  que abre a gaveta na busca (ignorado enquanto se digita).
- `app-shell/nav-drawer.tsx` (novo): gaveta `role="dialog"` com `inert` + `aria-hidden` quando fechada, foco no
  Fechar ao abrir, Tab preso, Esc e clique fora fecham com o foco voltando ao logo; busca sem acento com Enter
  para a primeira tela; seções com faixa `--nav-section`; itens em cascata; tema e Sair no pé.
- `nav-config.ts`: ícone lucide por módulo; o calendário aparece como "Calendário do dinheiro".
- `theme-toggle.tsx`: aceita `className` para seguir a cápsula.
- Verificado: `lint`, `tsc`, `build`; `scripts/e2e/e2e-m17-navegacao.mjs` 27/27 (contraste mínimo 5,9:1 no
  escuro); regressão `e2e-m16-tema`, `e2e-m16-calendario`, `e2e-m16-cores` e `e2e-m17-defeitos` ok.
  `e2e-m16-menu.mjs` removido: testava o cabeçalho antigo (botão "Menu" do celular, nome alinhado ao título).
- Contagem corrigida: são **21** telas (o calendário + 20).

**Etapa 3 (Resumo do mês) — feita em 2026-11-04, branch `marco-17-etapa-3-resumo`.**
- `app/(app)/dashboard/page.tsx`: título "Resumo de novembro" (com o ano fora do ano atual), ‹ Este mês ›;
  os avisos e o patrimônio só aparecem no mês atual, porque falam de hoje.
- `features/dashboard/month-summary.tsx` (novo):
  - `MonthHero`: o resultado do mês em mono grande; negativo em vermelho com "saiu mais do que entrou";
    mês sem lançamentos diz isso.
  - `buildNotices` + `AttentionList`: contas, faturas, seguros e dívidas numa lista só, a mais grave primeiro;
    bolinha de cor **e** a gravidade em texto para leitor de tela; cada linha leva à tela certa.
  - `CategoryBars`: barras horizontais em HTML numa cor só (`--chart-1`), do maior para o menor, valor escrito;
    acima de 8 categorias as menores viram "Outras (n)". Segue a skill de dataviz (série única, sem legenda,
    texto nas cores de texto).
  - `NetWorthLine`: patrimônio e a variação desde o fim do mês anterior, levando ao Balanço.
- Removidos (só o Resumo usava): `SummaryCards`, `CategorySpendingChart`, `BalanceEvolutionChart`,
  `CommitmentsAlert`, `CardsAlert`, `DebtsAlert`, `InsuranceAlert`, `NetWorthCard`.
- `lib/format.ts`: `monthName`, `shiftMonth`, `monthBounds` (o calendário passou a usar os mesmos).
- **Achado da etapa 2 corrigido:** no celular o Sair aparecia na cápsula (`inline-flex` vencia o `hidden`);
  agora só na gaveta, com checagem nova no `e2e-m17-navegacao`.
- Verificado: `lint`, `tsc`, `build`; `scripts/e2e/e2e-m17-resumo.mjs` 20/20. Roteiros antigos ajustados aos
  textos novos dos avisos (`e2e-m8-commitments`, `e2e-cards`, `e2e-m11`, `e2e-m15`), às barras em HTML
  (`e2e-m16-cores`) e ao título com o mês (`e2e-m17-defeitos`).
- **Pendência achada (não é desta etapa):** o Next 16 pede os arquivos de pré-carregamento com o nome "achatado"
  (`/calendar/__next.!KGFwcCk.calendar.__PAGE__.txt`) e o export grava em subpastas
  (`/calendar/__next.!KGFwcCk/calendar/__PAGE__.txt`): cada link visível gera um 404 no console e a navegação
  cai no carregamento normal. Funciona, mas é barulho e um pedido a mais por link (a gaveta tem 21). Já
  acontecia na tela de login. Correção provável: no nginx (e no `static_server.py`), trocar os pontos depois de
  `__next.` por barras; verificar antes de mexer.
- `e2e-m17-defeitos` deu um tempo esgotado uma vez na rodada em lote e passou 13/13 nas duas rodadas seguintes:
  anotado como possível instabilidade.

