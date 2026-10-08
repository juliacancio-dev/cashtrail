# CashTrail — Pesquisa de UI/UX: layout, cores e tipografia (FASE 21)

> Por que esta fase existe: a interface dos Marcos 2–7 foi construída com o tema **padrão** do shadcn/ui, sem pesquisa visual prévia. A [FASE 5](05-integrations.md) e a [FASE 2](02-market-research.md) compararam concorrentes por **funcionalidade**, nunca por layout/cor. Esta fase corrige isso, com fontes citadas. Nenhuma linha de UI será alterada antes das decisões da seção 5 serem aprovadas.

Legenda: **FATO** (fonte citada) · **HIPÓTESE** (proposta minha, a validar) · **NÃO ENCONTRADO** (não consegui verificar — não inventei).

---

## 1. O que foi pesquisado

| Referência | Tipo | Fonte primária obtida? |
|---|---|---|
| **Maybe** (finanças pessoais open-source, Rails+Tailwind) | Código real | **Sim** — tokens de cor e layout lidos direto do repositório |
| **Copilot Money** (iOS/Mac, referência de "mais bonito") | Análise de design | Parcial — paleta via análise de terceiros, não do app |
| **Nubank** | Marca | Parcial — cor primária; paleta secundária sem hex no artigo |
| **Monarch Money** | App comercial | Parcial — mudanças de layout/contraste do blog oficial; **sem hex** |
| **Actual Budget** | Código real | **Não** — tokens existem (`packages/component-library/src/themes`), mas não consegui ler os valores |
| **Mobills, Organizze, YNAB, Firefly III** | Apps | **NÃO ENCONTRADO** — as páginas de cor retornaram 404 / sem resultado útil |
| Boas práticas de dashboard financeiro e acessibilidade | Artigos | Sim (secundárias) |

**Limite honesto desta pesquisa:** consegui evidência forte de **dois** sistemas (Maybe e Copilot) e evidência parcial de outros três. Mobills e Organizze — os apps brasileiros mais próximos — não consegui analisar; para eles seria preciso ver o produto (screenshots/conta de teste), o que eu não consigo fazer daqui. Se você tiver prints de algum app que gosta, vale mais que qualquer artigo.

## 2. Achados

### 2.1 Layout (estrutura)

**FATO — Maybe** ([application.html.erb](https://raw.githubusercontent.com/maybe-finance/maybe/main/app/views/layouts/application.html.erb)):
- Desktop: **trilho de ícones fixo à esquerda (84px)** + **sidebar expansível (até 320px, colapsa com animação)** com a lista de contas + **conteúdo centralizado com `max-w-5xl`** e respiro lateral (`px-10`).
- Mobile: layout completamente diferente — **cabeçalho simples no topo + barra de navegação inferior fixa**.
- Fundo da página é a "surface" cinza claro; cartões brancos sobre ela.

**FATO — Monarch** ([blog oficial](https://www.monarch.com/blog/monarch-brand-refresh)): redesenharam a navegação lateral, deixaram a **sidebar colapsável**, adicionaram **breadcrumbs** nas páginas de detalhe e **reduziram o espaço em branco para aumentar densidade** em Dashboard/Contas/Lançamentos/Orçamento. Também refizeram o dark mode e **melhoraram contraste** a pedido dos usuários.

**FATO — Copilot** ([análise](https://blakecrosley.com/guides/design/copilot-money)): **divulgação progressiva** — a tela inicial é um resumo, **não uma planilha de lançamentos**; detalhes aparecem ao tocar nos gráficos. Superfícies separadas por **gradação de cor, sem bordas**.

**FATO — dashboards financeiros em geral** ([Eleken](https://www.eleken.co/blog-posts/financial-dashboard-examples)): estrutura recorrente em 3 camadas — **KPIs em cartões no topo → tendências/comparações no meio → detalhe/drill-down embaixo**. Linha para tendência, barras para comparação; **o artigo desaconselha gráfico de pizza** por legibilidade.

**Padrão que se repete nos três:** navegação lateral colapsável no desktop, barra inferior no mobile, resumo antes do detalhe, e conteúdo com largura máxima (não esticado na tela toda).

### 2.2 Cores

**FATO — Maybe** ([maybe-design-system.css](https://raw.githubusercontent.com/maybe-finance/maybe/main/app/assets/tailwind/maybe-design-system.css)): paleta **quase toda cinza neutra** (`#FAFAFA` → `#171717`, texto `#0B0B0B`); cor só onde há significado: sucesso `#10A861`, alerta `#DC6803`, erro `#EC2222`. Fonte **Geist**, raio 8–10px, sombras muito suaves (6% de preto). A regra do projeto: **usar tokens semânticos (`text-primary`, `bg-container`), nunca cor crua**.

**FATO — Copilot** (mesma análise): tema escuro com fundo **azul-marinho `#000814`** (não preto puro), superfícies `#001533`/`#00204D`, texto a **90% de branco** (cansa menos), **verde `#00CC4B` = receita, vermelho-laranja `#FF4433` = gasto, amarelo `#FECE4C` = pendente, azul `#1C6CFF` = interativo/patrimônio**. Princípio declarado: *cor semântica aplicada sempre do mesmo jeito*.

**FATO — Nubank** ([brand refresh](https://blog.nubank.com.br/brand-refresh-como-renovamos-a-identidade-visual-do-nubank/), [cor](https://www.brandcolorcode.com/nubank)): primária roxo **`#820AD1`**; a paleta é **cinzas, preto, branco e roxo** — "paleta bem reduzida". Fonte própria (NuSans).

**FATO — Monarch**: laranja vibrante como cor de marca; paletas claro/escuro revisadas para contraste.

**Padrão que se repete:** **neutros dominam; uma cor de marca; cores semânticas (verde/vermelho/amarelo) reservadas para dinheiro entrando/saindo/alerta.** Nenhum desses produtos usa o "cinza-azulado com botão preto" do shadcn padrão como identidade.

### 2.3 Acessibilidade das cores semânticas (conta feita por mim)

Calculei o contraste WCAG das cores que esses produtos usam:

| Combinação | Contraste | Texto pequeno (AA ≥ 4,5:1)? |
|---|---|---|
| Maybe verde `#10A861` sobre branco | **3,09:1** | **Não** |
| Maybe vermelho `#EC2222` sobre branco | 4,36:1 | **Não**, por pouco |
| Maybe alerta `#DC6803` sobre branco | 3,49:1 | **Não** |
| Maybe cinza `#9E9E9E` sobre branco | 2,68:1 | **Não** (só serve para decoração) |
| Copilot verde `#00CC4B` sobre `#000814` | 9,32:1 | Sim |
| Copilot vermelho `#FF4433` sobre `#000814` | 5,86:1 | Sim |

**Conclusão (FATO calculado):** verde/vermelho "de marca" funcionam bem em **fundo escuro**, mas em **fundo claro** precisam ser **mais escuros** para o valor monetário ser legível como texto. Além disso, [fontes de acessibilidade](https://medium.com/@courtneyjordan/designing-color-blind-accessible-dashboards-ba3e0084be82) recomendam **nunca usar só cor** para receita/despesa — somar **sinal (+/−), ícone ou rótulo**.

### 2.4 Diagnóstico da UI atual do CashTrail (FATO — código do repositório)

- Tema shadcn padrão (cinza-azulado, botão preto), **sem cor de marca**, sem identidade.
- Navegação: **linha de links de texto no topo** em cada página (`AppNav`), repetida página a página; sem sidebar, sem layout compartilhado, sem navegação mobile dedicada.
- Largura: cada página define a sua (`max-w-3xl`, `max-w-5xl`) — inconsistente.
- Dashboard: cartões + 2 gráficos, mas **sem hierarquia de KPI** nem divulgação progressiva.
- `/import` usa `<select>` nativo (desvio meu, já registrado).
- Cores de receita/despesa: verde/vermelho crus do Tailwind, **sem sinal/ícone consistente**.

## 3. O que NÃO ficou provado (hipóteses)

- **HIPÓTESE:** que tema claro como padrão é melhor que escuro para este caso. O Copilot (escuro) é a referência de "mais bonito", mas o Maybe e o Monarch priorizam claro com dark opcional; uso real de finanças é diurno/desktop. **Precisa da sua preferência.**
- **HIPÓTESE:** que o recrutador que abre a demo valoriza polimento visual (premissa do [07-stack.md](07-stack.md)) — é razoável, mas não medido.
- **DESCONHECIDO:** como Mobills/Organizze/YNAB resolvem layout e cor (ver seção 1).

## 4. Restrições do projeto que a UI precisa respeitar

- Next.js com **static export** (sem SSR), servido por nginx — qualquer abordagem precisa funcionar assim.
- Já usa Tailwind + shadcn/ui + Base UI + Recharts. **Não é preciso trocar de biblioteca**: o feio vem do **tema padrão**, não do shadcn em si — o próprio Maybe usa tokens semânticos sobre primitivos. Trocar tokens + layout é bem mais barato que reescrever componentes.
- Skill de dataviz do projeto já tem paleta categórica validada para os gráficos (usada no dashboard).

---

## 5. Decisões (aguardando aprovação)

### DECISÃO 1 — Estrutura de layout

- **ALTERNATIVAS:** (a) manter links de texto no topo de cada página; (b) **shell compartilhado: sidebar esquerda colapsável (desktop) + barra inferior (mobile) + conteúdo centralizado com largura máxima única**; (c) navegação só no topo, sem sidebar (padrão dos dashboards corporativos do artigo da Eleken).
- **EVIDÊNCIAS:** Maybe e Monarch convergem em (b); Monarch investiu especificamente em sidebar colapsável e breadcrumbs.
- **TRADE-OFFS:** (b) é a maior mudança estrutural (todas as páginas passam a viver dentro de um layout comum), mas **elimina** o `AppNav` repetido e a largura inconsistente — ou seja, reduz código. (c) é mais simples, mas escala mal: já são 9 itens de menu.
- **RECOMENDAÇÃO:** **(b)**.
- **CONFIANÇA:** Alta.

### DECISÃO 2 — Direção de cor (a que mais depende do seu gosto)

Todas as opções seguem o padrão encontrado: **neutros + 1 cor de marca + verde/vermelho/amarelo só para dinheiro**. Os hex abaixo são **proposta minha (HIPÓTESE)**, com contraste já calculado sobre branco:

| Opção | Inspirada em | Cor de marca | Contraste s/ branco | Clima |
|---|---|---|---|---|
| **A — Violeta** | Nubank (roxo `#820AD1`, contraste 7,21:1) | `#6D28D9` | 7,10:1 | Moderno, "fintech brasileira", reconhecível sem copiar a marca |
| **B — Azul** | Copilot (azul interativo) | `#1D4ED8` | 6,70:1 | Confiável, clássico, mais "banco" |
| **C — Laranja/terracota** | Monarch (laranja de marca) | `#C2410C` | 5,18:1 | Quente, acolhedor, mais diferente |

Para **receita/despesa em fundo claro**, proponho tons escuros o bastante para texto: verde `#0B7A4B` (5,39:1) e vermelho `#C62828` (5,62:1) — sempre **acompanhados de sinal (+/−) e ícone**, nunca só cor.

- **RECOMENDAÇÃO:** **A (violeta)**.
- **POR QUÊ:** dá identidade própria e é o que mais se parece com o ecossistema financeiro brasileiro (público provável da demo), com o melhor contraste dos três. Mas **é gosto, não fato**: se você prefere B ou C, qualquer um é defensável.
- **CONFIANÇA:** Média (a escolha é subjetiva).
- **O QUE PRECISA SER VALIDADO:** ver as três direções aplicadas numa tela real (protótipo) antes de fechar.

### DECISÃO 3 — Tema claro, escuro, ou os dois

- **ALTERNATIVAS:** (a) só claro; (b) claro + escuro com alternância; (c) só escuro (estilo Copilot).
- **EVIDÊNCIAS:** Maybe e Monarch oferecem os dois; Monarch refez o dark mode por feedback de contraste; os valores escuros que calculei (`#34D399` sobre `#0B1020` = 9,85:1; vermelho `#F87171` = 6,84:1) funcionam bem.
- **TRADE-OFFS:** (b) dobra os tokens a manter, mas com tokens semânticos o custo é baixo (o projeto já tem a estrutura de tokens do shadcn).
- **RECOMENDAÇÃO:** **(b)**, claro como padrão.
- **CONFIANÇA:** Média.

### DECISÃO 4 — Tipografia

- **ALTERNATIVAS:** (a) fonte padrão do sistema; (b) **Geist** (usada pelo Maybe; open-source, com variante mono); (c) fonte de marca própria (inviável).
- **RECOMENDAÇÃO:** **(b) Geist + Geist Mono** para valores monetários (alinhamento de casas decimais em tabelas).
- **CONFIANÇA:** Média-alta.

### DECISÃO 5 — Estrutura do Dashboard

- **RECOMENDAÇÃO:** seguir as 3 camadas da pesquisa — **KPIs no topo (saldo, receitas, despesas, resultado do mês) → tendência (linha) e comparação por categoria (barras, **sem pizza**) → últimos lançamentos com ação "ver todos"**. Orçamentos estourados como alerta visível no topo.
- **CONFIANÇA:** Alta (padrão convergente).

### DECISÃO 6 — Como executar sem reescrever tudo

- **RECOMENDAÇÃO:** (1) definir **tokens semânticos** (estilo Maybe) + fonte; (2) criar o **shell de layout** compartilhado; (3) migrar página por página (começando por Dashboard e Lançamentos, que são a vitrine); (4) trocar os `<select>` nativos do `/import` pelo `Select` do projeto. **Uma branch por etapa**, como você prefere.
- **CONFIANÇA:** Alta.

---

**STATUS:** Ainda não pronto — faltam suas decisões (principalmente a 2 e a 3, que são de gosto).

**PENDÊNCIAS:**
1. Escolher a direção de cor (A/B/C) — ou pedir o protótipo visual das três antes de decidir.
2. Escolher claro / escuro / os dois.
3. Se tiver prints de apps que você gosta (Mobills, Organizze, Nubank, outros), enviar — cobre a lacuna da seção 1.
4. Confirmar a ordem de execução (Decisão 6).
