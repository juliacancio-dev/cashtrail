# Marco 17 — Acabamento: Resumo do mês e telas densas no estilo calmo

> Status: **APROVADO pela Julia em 2026-11-04** (decisões 1 a 7 como recomendadas). Etapa 1 feita.
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

## 4. Plano (uma branch por etapa, merge `--no-ff` no fim do marco)

| Etapa | O que | Verificação |
|---|---|---|
| 1. Defeitos | A1 (backend, um ponto por dia + teste), A3, A4, A5, A6 | `pytest` da slice `dashboard`; teste do fuso no navegador com `timezoneId` em America/Sao_Paulo às 22h; `lint`/`tsc`/`build` |
| 2. Resumo do mês | Decisões 1 e 2 | roteiro de navegador nos dois temas, números conferidos com a API |
| 3. Lançamentos | Decisão 3 | roteiro: troca de mês, agrupamento por dia, criar lançamento, celular sem rolagem horizontal |
| 4. Compromissos | Decisão 4 | roteiro: filtros, agrupamento, pagar, editar, desfazer baixa (repete o e2e do Marco 8) |
| 5. Cartões | Decisão 5 | roteiro: fatura atual aberta, pagar fatura, mover compra (repete o e2e do Marco 9) |

**Estimativa (por analogia com o Marco 16, não medida):** 14 a 24 horas; a etapa 4 é a maior.

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
