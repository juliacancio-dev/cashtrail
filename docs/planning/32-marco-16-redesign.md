# CashTrail — Marco 16: redesign (calendário calmo, claro e escuro)

> Desenho para aprovação. **Nenhum código de interface foi alterado.** Branch `marco-16-redesign`. Referência visual aprovada pela Julia em 2026-10-23: o conceito **K** do artifact "CashTrail — conceitos de redesign" (calendário calmo com linha de saldo fina), **com modo claro e escuro**. O caminho até ele está no doc 21 (rounds 2 a 5).

Legenda: **FATO** (verificado no código, no protótipo ou por cálculo) · **INFERÊNCIA** · **DESCONHECIDO**.

## 1. Objetivo e critério de saída

**Objetivo:** trocar a interface padrão do shadcn por uma identidade própria e calma, com o **calendário do dinheiro** como tela inicial e **modo claro e escuro**, sem perder nenhuma funcionalidade dos Marcos 1 a 15.

**Pronto quando:**
- Ao entrar, a pessoa cai no calendário: saldo de hoje, uma frase com o dia mais apertado do mês, a linha de saldo fina, o calendário do mês e o detalhe do dia ao clicar.
- O menu tem **6 entradas** (Calendário + 5 módulos) e não quebra em duas linhas; as 20 telas continuam acessíveis.
- Botão de tema no cabeçalho; o tema escolhido fica salvo; sem "piscar" o tema errado ao abrir a página.
- Todas as telas existentes herdam as cores novas nos dois temas, com contraste AA.
- Backend: testes da rota nova passando; frontend: `lint`, `tsc` e `build` limpos; roteiro de navegador do calendário nos dois temas.

## 2. O que já existe (FATO, conferido no código)

| Item | Estado hoje | Consequência |
|---|---|---|
| Fonte | `layout.tsx` já carrega **Geist** e **Geist Mono** (as mesmas do K), mas **não aplicava**: `globals.css` tinha `--font-sans: var(--font-sans)`, que aponta para si mesmo e invalida a variável (achado na etapa 1, corrigido para `var(--font-geist-sans)`) | Só a correção |
| Tokens de tema | `globals.css` tem as variáveis do shadcn em `:root` e em `.dark`, e a variante `dark` por classe | Trocar os valores **repinta as 20 telas de uma vez** |
| Tema escuro | Os tokens existem, mas **nada liga a classe `dark`** e não há botão | Falta o mecanismo (decisão 3) |
| Menu | `components/app-nav.tsx`: 20 links soltos, repetido em cada página | Vira o shell compartilhado (decisão 2) |
| Dados do calendário | `reports/cash_flow.py` → `collect_items` já monta os itens **realizados e previstos** por data (lançamentos em contas de caixa, contas a pagar e a receber, faturas, recorrências expandidas), e `_opening_total` dá o saldo inicial | A rota nova só agrega por dia (decisão 4) |
| Tela inicial | `/dashboard` (cartões, gráficos, alertas) | Decisão 1 |
| `lang` do HTML | `layout.tsx` declara `lang="en"`, mas o app é todo em português | Corrigir para `pt-BR` junto |

## 3. Decisões

### DECISÃO 1 — Qual é a tela inicial

- **ALTERNATIVAS:** (a) **o calendário vira a tela inicial**, e o dashboard atual vira "Resumo do mês" dentro de Caixa; (b) o calendário entra como uma tela a mais, e o dashboard continua sendo a inicial; (c) calendário e dashboard fundidos numa página só.
- **EVIDÊNCIAS:** foi o K que ela aprovou, e ela recusou o round 4 por estar "poluído". A (c) repete esse erro.
- **TRADE-OFFS:** (a) muda o hábito de quem já usa (só ela, dados de teste — D5), mas é a única que entrega o conceito aprovado. (b) é a mais segura e esconde o redesign atrás de um clique.
- **RECOMENDAÇÃO:** **(a)**. O login e a rota `/` passam a levar a `/calendar`; `/dashboard` continua existindo, com o nome "Resumo do mês".
- **CONFIANÇA:** Alta.

### DECISÃO 2 — Navegação com 6 entradas

Agrupamento usado em todos os protótipos (ela não contestou):

| Entrada | Telas |
|---|---|
| **Calendário** | `/calendar` (nova) |
| **Caixa** | Resumo do mês (`/dashboard`), Lançamentos, Categorias, Transferências, Importar extrato |
| **Compromissos** | A pagar e a receber, Cartões e faturas, Recorrências, Dívidas |
| **Patrimônio** | Contas, Bens, Investimentos, Patrimônio (balanço) |
| **Planejamento** | Orçamentos, Metas, Independência, Seguros |
| **Relatórios** | DRE, Fluxo de caixa, Imposto de renda |

Categorias fica em Caixa, logo depois de Lançamentos, porque é o cadastro que os lançamentos usam.

- **ALTERNATIVAS:** (a) **6 links no topo + uma linha de abas do módulo** logo abaixo do cabeçalho, só nas páginas daquele módulo; (b) 6 links no topo, cada um abrindo um menu suspenso; (c) barra lateral com grupos.
- **TRADE-OFFS:** (a) é o que o K mostra, fica calmo e funciona sem clique extra; custa uma faixa a mais de altura nas páginas de módulo. (b) esconde as telas atrás de um clique e é pior no celular. (c) contraria o visual aprovado (o K não tem barra lateral).
- **RECOMENDAÇÃO:** **(a)**. No celular, os 6 links viram um botão "Menu" que abre a lista, e as abas do módulo rolam na horizontal.
- **CONFIANÇA:** Média-alta (o K só mostra o topo; as abas do módulo ainda não foram vistas por ela).
- **O QUE PRECISA SER VALIDADO:** ver as abas do módulo numa tela (dá para desenhar no protótipo antes do código).

### DECISÃO 3 — Modo claro e escuro (pedido dela)

- **ALTERNATIVAS:** (a) **seguir o sistema na primeira visita, com botão para trocar, e guardar a escolha** no navegador; (b) só o botão, começando sempre no claro; (c) só seguir o sistema, sem botão.
- **Mecanismo** (o app é export estático, sem servidor): (i) biblioteca **`next-themes`**; (ii) um script próprio de poucas linhas no `<head>` que aplica a classe `dark` antes da página pintar, mais um botão que troca e salva.
- **TRADE-OFFS:** `next-themes` resolve o "piscar" e a sincronia entre abas, mas é uma dependência a mais. O script próprio são ~15 linhas sem dependência, e precisa de cuidado: rodar antes da primeira pintura, `try/catch` no `localStorage`, `suppressHydrationWarning` no `<html>`.
- **RECOMENDAÇÃO:** **(a) com script próprio (ii)**. É pouco código, fácil de defender numa revisão, e não depende de uma biblioteca para algo tão pequeno.
- **CONFIANÇA:** Média (as duas opções funcionam; é preferência de manutenção).

### DECISÃO 4 — Dados do calendário: uma rota nova de leitura

`GET /reports/calendar?month=AAAA-MM` na slice `reports` (de leitura; sem tabela nova e sem migração). Para cada dia do mês: data, **saldo em caixa no fim do dia**, se é realizado ou previsão, se teve movimento e a lista dos movimentos (descrição, valor, tipo, origem). No topo: saldo de hoje, **dia mais apertado do mês** (menor saldo; em empate, o primeiro) e a série da linha fina.

- **Como calcula (reuso, sem regra nova):** saldo inicial das contas de caixa (`_opening_total`) + itens de `collect_items` acumulados por dia. Valem as regras que já existem no fluxo de caixa: compra no cartão não mexe no caixa, só o pagamento da fatura; transferência entre contas de caixa não muda o saldo total; o que está atrasado aparece como pendente hoje.
- **ALTERNATIVAS:** (a) **rota nova que agrega por dia no backend**; (b) o frontend chama `/reports/cash-flow/items` e soma por dia.
- **TRADE-OFFS:** (a) mantém a conta de dinheiro no backend, onde há testes de propriedade, e deixa o frontend simples. (b) evita uma rota, mas espalha conta de dinheiro no navegador, que não tem teste unitário.
- **RECOMENDAÇÃO:** **(a)**.
- **Testes de propriedade propostos:** o saldo de hoje no calendário é igual ao `cash_total` de `/reports/balances`; o saldo do último dia é igual ao saldo inicial do mês mais a soma de todos os movimentos do mês.
- **Como ficou (etapa 3, 2026-10-29):** `reports/calendar_view.py` + `GET /reports/calendar?month=AAAA-MM` (padrão: mês atual), 14 testes em `tests/test_calendar.py`. Regra do dia: saldo no fim do dia d = saldo inicial + realizados até d + o que resta dos previstos entre hoje e d. Por isso o **dia de hoje** mostra o saldo **depois** do que vence hoje ou está vencido e não pago, enquanto `cash_today` (o número grande do topo) é só o realizado e bate com `/reports/balances`. Propriedades testadas: `cash_today` = `cash_total`; cada dia = anterior + movimento do dia; o mês seguinte abre onde este fechou; o fechamento do mês = `closing_projected` do fluxo de caixa. "Dia apertado" = os `ceil(dias/4)` menores saldos (empates entram); mês sem variação não tem dia apertado. **Ajuste na etapa 4:** se os empates no valor de corte passarem de um quarto do mês (saldo parado por semanas), só entram os dias abaixo dele; sem isso, um mês com o saldo parado de 02 a 30 marcava 30 de 31 dias.
- **CONFIANÇA:** Alta.

### DECISÃO 5 — O que a previsão não sabe

**FATO:** a previsão só conhece o que está **agendado** (contas a pagar e a receber, recorrências e faturas). Mercado, combustível e outros gastos do dia a dia ainda não lançados não entram, então o futuro parece mais folgado do que vai ser.

- **ALTERNATIVAS:** (a) **avisar numa frase curta no detalhe de um dia de previsão** ("previsão com o que está agendado"); (b) avisar fixo embaixo do calendário; (c) não avisar.
- **TRADE-OFFS:** (a) informa sem poluir a tela principal (o motivo de ela ter recusado o round 4). (b) é mais visível, mas é mais um texto permanente. (c) é enganoso.
- **RECOMENDAÇÃO:** **(a)**. Melhorar a previsão (por exemplo, com a média dos gastos variáveis) fica no backlog.
- **CONFIANÇA:** Alta.

### DECISÃO 6 — Paleta e contraste (FATO calculado)

Tokens do K aplicados às variáveis do shadcn que já existem (`--background`, `--foreground`, `--muted-foreground`, `--border`, `--primary` ...), mais 2 tokens novos: `--accent-money` (hoje, ponto selecionado) e `--tight` (fundo dos dias apertados).

| Uso | Claro | Escuro |
|---|---|---|
| Fundo | `#FAFAF9` | `#111113` |
| Texto | `#18181B` — 16,96:1 | `#EDEDEF` — 16,13:1 |
| Texto apagado | `#5C5C66` — 6,33:1 | `#A1A1AA` — 7,36:1 |
| Borda | `#E4E4E7` | `#27272A` |
| Destaque (hoje) | `#A84D08` — 5,39:1 (5,03:1 sobre dia apertado) | `#F2B53A` — 10,28:1 (8,41:1 sobre dia apertado) |
| Dia apertado (fundo) | `#FBF1E1` | `#2A2414` |
| Selecionado | fundo `#18181B`, texto `#FAFAF9` | fundo `#EDEDEF`, texto `#111113` |

Contrastes calculados pela fórmula WCAG em 2026-10-23. O destaque claro do protótipo (`#B45309`) dava **4,49:1** sobre o dia apertado, abaixo do mínimo de 4,5:1; troquei por `#A84D08` no protótipo e aqui.

- **O QUE PRECISA SER VALIDADO:** as cores de **receita, despesa e transferência** nas telas densas (lançamentos, DRE) e as **cores dos gráficos** (Recharts) nos dois temas. O K quase não usa verde e vermelho; as outras telas precisam. Escolher na etapa 5, sempre com sinal + e −, nunca só cor.
- **"Dia apertado":** no protótipo, abaixo de R$ 12.500 (valor fixo de exemplo). Proposta para o código: os dias com saldo no **quarto mais baixo do mês** (relativo, funciona para qualquer renda). **CONFIANÇA:** Média; é regra nova, ela decide.

## 4. Fora do escopo (backlog)

- **Colchão** (o mínimo em caixa, conceito H): configuração nova por usuário e alerta "a previsão fura o colchão no dia X".
- Previsão com média de gastos variáveis.
- Redesenho tela a tela das 20 páginas no estilo calmo (este marco repinta pelas cores e troca o menu); cada tela densa vira um passo próprio depois.
- Visões que ela viu e não escolheu (jornal, rio, nível).

## 5. Plano de implementação (uma branch por etapa)

| Etapa | O que | Verificação |
|---|---|---|
| 1. Tokens e tema | Valores novos em `globals.css` (claro e escuro), script de tema no `<head>`, botão, `lang="pt-BR"` | `build`; abrir 3 telas nos dois temas; contraste conferido |
| 2. Shell e menu | Layout compartilhado com os 6 links + abas do módulo; remover o `AppNav` repetido das 20 páginas; menu de celular | Roteiro de navegador: as 20 rotas abrem pelo menu; largura de celular sem rolagem horizontal |
| 3. Rota do calendário | `GET /reports/calendar` + testes (incluindo os de propriedade da decisão 4) | `pytest` da slice `reports` |
| 4. Tela do calendário | `/calendar` como no K: saldo, frase, linha fina, calendário, detalhe ao clicar, troca de mês; vira a tela inicial | Roteiro de navegador nos dois temas, com números conferidos à mão |
| 5. Cores de dinheiro e gráficos | Receita, despesa e transferência e paleta dos gráficos nos dois temas | Lançamentos, DRE e fluxo nos dois temas |

**Estimativa (por analogia com os Marcos 8 a 10, não medida):** 20 a 34 horas no total; a etapa 2 é a maior, porque mexe nas 20 páginas.

## 6. Riscos

| Risco | Mitigação |
|---|---|
| Tema "pisca" ao abrir (export estático) | Script no `<head>` antes da pintura (decisão 3) |
| Telas antigas com cores fixas (`text-green-600` etc.) ficam ruins no escuro | Procurar as cores cruas na etapa 1 e trocar por tokens |
| Recharts com cores fixas no escuro | Etapa 5 |
| Mês com muitos lançamentos deixa o calendário lento | Uma chamada por mês; medir com um mês grande de teste |
| Ela não gostar das abas do módulo (ainda não vistas) | Desenhar no protótipo antes da etapa 2 |

**APROVADO pela Julia em 2026-10-26:** decisões 1 a 6 como recomendadas, incluindo "dia apertado" = saldo no quarto mais baixo do mês; ela quer ver as abas do módulo no protótipo antes da etapa 2 (artboard "L — Caixa › Lançamentos").

## STATUS

**Etapa 1 (tokens e tema) — feita em 2026-10-26, branch `marco-16-etapa-1-tema`.**
- `globals.css`: paleta da decisão 6 em `:root` e `.dark`, tokens novos `accent-money` e `tight`; foco (`--ring`) na cor de destaque.
- `layout.tsx`: script de tema no `<head>` (escolha salva, senão o sistema), `suppressHydrationWarning`, `lang="pt-BR"`.
- `components/theme-toggle.tsx`: botão com `useSyncExternalStore` observando a classe do `<html>` (sem `setState` em efeito); salva em `localStorage` com `try/catch`. Por enquanto fica no fim do `AppNav`; vai para o cabeçalho na etapa 2.
- **Achado:** a fonte Geist era baixada e nunca aplicada (`--font-sans: var(--font-sans)`); corrigido.
- **Anotado para a etapa 5:** `text-green-600` das receitas dá 3,16:1 no fundo claro (já reprovava antes); os gráficos têm cores fixas em hex.
- Verificado: `lint`, `tsc` e `build` limpos; `scripts/e2e/e2e-m16-tema.mjs` com 10/10 (tema do sistema aplicado antes da hidratação, fundo certo nos dois temas, `lang`, fonte, botão troca e salva, escolha vence o sistema depois de recarregar).

## 7. Pendências para a Julia

1. Aprovar ou ajustar as decisões 1 a 6 (principalmente a 1, a 2 e a regra do "dia apertado").
2. Dizer se quer ver as **abas do módulo** no protótipo antes da etapa 2.
3. Confirmar a ordem das etapas.
