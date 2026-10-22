# CashTrail — contexto completo para continuar em outra máquina

Legenda: **FATO** (verificado no código, no portal ou numa fonte) · **INFERÊNCIA** · **DESCONHECIDO**.

---

## 0. Como usar este documento

1. Clone o repositório (`juliacancio-dev/cashtrail`) e abra a pasta no Claude Code.
2. Cole o **prompt de retomada** abaixo na primeira mensagem.
3. O assistente deve ler este arquivo, `docs/planning/31-checklist-pre-deploy.md` e o doc do marco em andamento antes de agir.

### Prompt de retomada (copie e cole)

```
Estou retomando o projeto CashTrail em outra máquina. Leia primeiro docs/CONTEXTO-PARA-CONTINUAR.md
e docs/planning/31-checklist-pre-deploy.md. Siga as regras de trabalho da seção 1 (principalmente: nunca
faça git commit/push por mim, crie uma branch por fase, decisões no formato DECISÃO/ALTERNATIVAS/TRADE-OFFS,
e não mexa no Azure sem eu pedir). Estamos no meio da sessão de deploy no Azure: o ponto exato está na
seção 12. Confirme o estado do git e me diga qual é o próximo passo.
```

---

## 1. Quem é a Julia e como trabalhar com ela (regras permanentes)

- Fala **português do Brasil**. Usa **PowerShell** no Windows (não Git Bash): variáveis de ambiente em linha são `$env:VAR="valor"; comando`.
- O CashTrail é o app de finanças pessoais **e** peça principal de portfólio dela (mostra API, testes e deploy em nuvem na stack Python). Ela pretende **usar de verdade** no dia a dia.
- **Ela quer entender e defender cada decisão** numa reunião ou revisão de código sem depender da IA. Por isso:
  - **Descoberta antes de código**: nada de código de produção antes de desenho e decisões aprovadas (existe um processo em fases e gates, de FASE 0 a 18; todo marco novo começa com um doc de desenho em `docs/planning/`).
  - **Formato das decisões**: `DECISÃO / ALTERNATIVAS / EVIDÊNCIAS / TRADE-OFFS / RECOMENDAÇÃO / POR QUÊ / CONFIANÇA (Baixa/Média/Alta) / O QUE PRECISA SER VALIDADO`. Nunca escolher em silêncio algo que ela precise defender.
  - **Classificar afirmações**: FATO, HIPÓTESE, INFERÊNCIA, DESCONHECIDO. Não promover hipótese a requisito.
  - **Pesquisar antes de afirmar** fatos externos (APIs, preços, limites, regras fiscais) com fonte e data, preferindo documentação oficial; escrever "não encontrado / precisa ser validado" em vez de inventar.
  - Não superdocumentar: cada documento existe para ajudar uma decisão real.
- **Git**: o assistente **nunca** faz `git commit`, `git push` nem merge por ela, em nenhum repositório. Ela faz tudo à mão para os commits não levarem coautoria do assistente. O assistente pode criar arquivos e **criar branches** (`git checkout -b`). Branch por fase com o nome `marco-<n>-<slug>`.
- **Antes de um commit**, avisar que `frontend/AGENTS.md` e `CLAUDE.md` não devem entrar se reaparecerem.
- **Azure**: só mexer quando ela pedir. Deploy em **lote** (não por marco). "Só vou mexer na Azure quando TUDO estiver pronto." O assistente **não tem Azure CLI** nesta máquina: ela executa no portal/GitHub e cola as saídas (nunca cole segredos).
- **Interface**: não aceitou o visual padrão do shadcn; quer algo **autêntico, não um template genérico recolorido**. A interface atual é **funcional**; o redesign é um marco futuro, e depende de ela mandar capturas de ERPs (ver seção 13).
- **Visão do produto** (2026-10-06): "um ERP pessoal foda, tipo o do Bling", no sentido de **integração ponta a ponta da vida financeira pessoal** (lança uma vez e alimenta tudo). **Não** é vendas, estoque, NF-e, nem documentos/agenda/tarefas.
- **Decisão sobre e-mail** (2026-10-08): manter o **Azure Communication Services (ACS) Email**, mesmo sabendo que ele é aposentado em **2028-09-30**. Não reabrir.

---

## 2. O projeto em uma página

- **Repositório**: `juliacancio-dev/cashtrail`, pasta local `C:\Users\julia.jesus\Documents\projetos-pessoais\cashtrail`.
- **Estado em 2026-10-22**: os **Marcos 1 a 15 estão implementados e em produção**. O workflow *Deploy* rodou com sucesso em **2026-10-15 18:56 UTC** com o commit `bbe1b52`, e de novo em 2026-10-22 com o commit `acc0956` (e-mail pelo ACS ligado e testado). Roteiro de fumaça feito em 2026-10-22 (seção 12).
- **Testes**: 735 no backend (Testcontainers com Postgres real), lint/tsc/build do frontend limpos.
- **Módulos** (visão do usuário): contas, categorias, lançamentos, dashboard, orçamentos, metas, recorrências, importação de extrato CSV, recuperação de senha, contas a pagar/receber, transferências, cartões e faturas, saldo por conta, DRE, fluxo de caixa, dívidas e financiamentos, bens, patrimônio, investimentos, imposto de renda (apoio à declaração), seguros e independência financeira.

---

## 3. Stack e arquitetura

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16, APScheduler (jobs dentro do processo, ADR-005), slowapi (limite de login), `argon2` para senhas, JWT.
- **Frontend**: Next.js 16 com **export estático** (`output: "export"`), Tailwind, shadcn com **Base UI** (o `Select` precisa da prop `items`, e `onValueChange` pode devolver `null`), react-hook-form + zod, Recharts. Servido por **nginx** num Container App.
- **Nuvem**: Azure Container Apps (ambiente **Express**), Azure Container Registry (Basic), PostgreSQL Flexible Server, Key Vault. CI/CD em **GitHub Actions** com login OIDC.
- **Vertical slices**: cada funcionalidade é uma pasta completa em `backend/src/features/<nome>/` (modelo, schema, repositório, serviço, rota e testes juntos). Regras de dependência (ADR-007, `docs/planning/09-vertical-slices.md`):
  - `transactions` é o núcleo; outras slices dependem **só do `service` público** de outra slice, **nunca** do repositório ou modelo ORM dela.
  - Slices de leitura (`dashboard`, `reports`) não têm modelo próprio e **ninguém depende delas**, exceto `tax` (que lê `reports.net_worth`).
  - Evitar dependência circular (ex.: `accounts` não calcula saldo porque `transactions` depende de `accounts`).
- **Slices atuais**: `auth`, `accounts`, `categories`, `transactions`, `dashboard`, `budgets`, `goals`, `recurring`, `statement_import`, `commitments`, `transfers`, `credit_cards`, `debts`, `assets`, `investments`, `tax`, `insurance`, `retirement`, `reports`.
- **Dinheiro**: `amount` é sempre positivo e a direção vem do tipo; `Numeric` com 2 casas; arredondamento explícito; testes de propriedade onde há soma ou cálculo.

---

## 4. Mapa dos marcos

| Marco | Entrega | Slices / tabelas principais | Notas |
|---|---|---|---|
| 1 | Descoberta e documentação | `docs/planning/00` a `20`, ADRs | processo de fases e gates |
| 2 | Auth + contas + 1º deploy | `auth`, `accounts` | cookie de refresh `httpOnly`; frontend containerizado (Static Web Apps bloqueado por política da assinatura) |
| 3 | Categorias, lançamentos, dashboard | `categories`, `transactions`, `dashboard` | |
| 4 | Orçamentos e metas | `budgets`, `goals` | meta recebe aporte por endpoint próprio |
| 5 | Recorrências | `recurring` | job diário; `ENABLE_SCHEDULER` |
| 6 | Hardening | rate limit, CSRF | **MVP completo**, **implantado em 2026-09-28** |
| 7 | Recuperação de senha + importação CSV | `statement_import`, tokens de reset | e-mail via ACS (código pronto, não testado no Azure) |
| 8 | Contas a pagar e a receber | `commitments`, `commitment_settlements` | baixa gera lançamento; recorrência pode gerar contas |
| 9 | Transferências, cartões e faturas | `transfers`, `credit_cards` | fatura **derivada**, pagar fatura é **transferência** |
| 10 | Saldo inicial, DRE, fluxo de caixa | `reports` (leitura) | `accounts.opening_balance`, `categories.dre_group` |
| 11 | Dívidas e financiamentos | `debts` | conta tipo `loan`; baixa separa principal e encargos; amortização com recálculo |
| 12 | Bens e patrimônio | `assets`, `reports.net_worth` | avaliações por data, patrimônio histórico calculado |
| 13 | Investimentos | `investments` | conta tipo `investment`; brapi + Banco Central |
| 14 | Imposto de renda | `tax` | apoio à declaração; parâmetros por ano |
| 15 | Seguros e independência financeira | `insurance`, `retirement` | prêmio entra no fluxo; simulador em valores reais |

Cortes planejados: v2 = 8 a 10, v3 = 11 e 12, v4 = 13 a 15.

---

## 5. Regras de domínio que não podem ser quebradas

- **Transferência não é receita nem despesa** (RB-014): fica fora de dashboard, orçamentos, metas e DRE. Pagar fatura de cartão, receber um empréstimo, amortizar principal e comprar investimento são **transferências**.
- **Compra no cartão é despesa na data da compra**; o **pagamento da fatura** é transferência (senão conta em dobro). A fatura é identificada pela **data de fechamento**; compra no dia do fechamento entra na fatura que fecha; vencimento = primeira data estritamente depois do fechamento com o dia de vencimento; dias 29 a 31 viram o último dia do mês.
- **DRE é por competência; fluxo de caixa é por caixa.** "Contas de caixa" = contas que **não** são `credit_card`, `loan` nem `investment` (constante central `NON_CASH_TYPES` em `accounts/models.py`).
- **Fluxo de caixa**: realizado (data ≤ hoje) × previsto (contas a pagar/receber, faturas, recorrências expandidas) × projetado = realizado + o que falta; atrasado vira pendente no mês corrente.
- **Dívida**: saldo devedor = −saldo da conta `loan`. Baixa da parcela = transferência do **principal** + despesa dos **encargos**; parcela de dívida **não** pode ser paga/editada/cancelada pelas rotas genéricas de `/commitments` (409, use `/debts`). Amortização extra regera as parcelas em aberto (padrão: reduzir prazo, opção reduzir parcela); não tem "desfazer".
- **Patrimônio** = caixa + bens (valor de avaliação em cada data) + investimentos (**valor de mercado**) − cartões − dívidas. O saldo da conta `investment` (custo) fica **fora** (evita contar em dobro). Antes da primeira avaliação um bem vale zero; venda/baixa do bem zera a partir da data.
- **Investimentos**: compra = transferência caixa → conta de investimento (taxas entram no custo); venda = transferência do **custo** de volta + ganho (receita financeira) ou perda (despesa financeira) lançados **uma vez**; provento = receita financeira; valorização **não** é receita; custo médio ponderado móvel; só a **última** operação do ativo pode ser desfeita e as operações precisam ser cronológicas.
- **IRPF**: três regimes que não se misturam (declaração anual com tabela progressiva; ganho de capital em renda variável com DARF mensal fora da base; isentos). Salário, 13º, PLR e renda fixa vêm do **informe de rendimentos digitado** (o sistema não recalcula). Bens e direitos em 31/12 pelo **custo**, não pelo valor de mercado. Sem CPF de ninguém armazenado.
- **Seguros/aposentadoria**: prêmio mensal vira recorrência (que gera conta a pagar) e anual vira conta a pagar na renovação; **simulação sempre em valores reais**, taxa de retirada e retorno são **premissas editáveis**, INSS não é calculado.
- **Enums do Postgres guardam o NOME do membro** (`LOAN`, `INVESTMENT`), não o valor (`loan`). Para novos conjuntos de valores, prefira **texto com CHECK**, não enum nativo (o projeto já teve problema três vezes).

---

## 6. Decisões grandes (resumo; detalhes nos docs)

- **Azure** como nuvem (ADR-001) — a conversa original tinha AWS em documentos antigos, resolvido a favor do Azure.
- **Multiusuário desde o início** (ADR-002); **SQLAlchemy** em vez de SQLModel (ADR-003); **autenticação própria** (ADR-004); **APScheduler** em vez de Celery (ADR-005); **JWT em memória + cookie `httpOnly`** para o refresh (ADR-006); **transações como núcleo** das slices (ADR-007).
- **Frontend em Container Apps** com export estático e nginx (Static Web Apps indisponível na assinatura Azure for Students).
- **E-mail**: ACS (decisão dela, ver seção 1).
- **Banco ligado** todo dia das **06:00 às 23:00 (Brasília)**: `db-lifecycle.yml` liga às 09:00 UTC e desliga às 02:00 UTC (decisão D1 de 2026-10-15; ver o aviso de custo na seção 12).
- **Cotações automáticas**: brapi (plano grátis) com cache, teto mensal e valor manual sempre possível; **deploy sem token** na primeira vez (D3).
- **Interface**: publicar agora com a UI atual, redesign depois (D4).
- **Dados em produção** são só de teste/demo (D5).
- **Marco 11, decisão 4**: incluir amortização com recálculo (a recomendação era deixar fora; ela escolheu incluir).

---

## 7. Estado do Git

- A `main` contém **todos** os marcos 7 a 15 e o commit `bbe1b52` ("banco ligado todo dia 06h-23h e decisoes de pre-deploy"). `git status` limpo em 2026-10-17. **Não confirmei** se o `git push origin main` foi feito (ela deve conferir com `git log origin/main -1`).
- Existem branches locais antigas por marco (`marco-8-...` a `marco-15-...`, `marco-7-...`, `cd-deploy-azure`); todas já estão contidas na `main` e podem ser apagadas depois.
- Commits relevantes: `f1344ab` merge do Marco 7; `c45216f` Marco 9; `d83ce4d` Marco 11; `194f9f1` Marco 12; `86fa5bc` Marco 13; `41c50b7` Marco 14; `df5e3b1` Marco 15; `409bca5` checklist de pré-deploy + token da brapi no deploy + cotações na subida; `bbe1b52` agenda do banco.
- **Arquivos novos desta sessão que ela ainda precisa commitar**: `docs/CONTEXTO-PARA-CONTINUAR.md` e `scripts/e2e/` (roteiros de navegador).

---

## 8. Banco e migrações

Cadeia de migrações (em `backend/alembic/versions/`, em ordem). As acima da linha subiram no deploy de 2026-09-28; **as 12 abaixo da linha subiram no deploy de 2026-10-15** (o backend novo está de pé, então todas aplicaram).

| Revisão | Marco | O que faz |
|---|---|---|
| `f30ba74d5b54` | 2 | usuários e contas |
| `f960bb5ff835` | 3 | categorias e lançamentos |
| `b6be3270c643` | 4 | metas e orçamentos |
| `5794659919a8` | 5 | recorrências |
| — | — | **linha do deploy de 2026-09-28** |
| `a1c9e4d27f10` | 7 | tokens de recuperação de senha |
| `c3e8b1f05a92` | 7 | `statement_imports` |
| `d4a7c2e91b36` | 8 | compromissos e baixas |
| `e5b8d3f02c47` | 8 | recorrência gera compromisso |
| `f6c9e4a13d58` | 9 | transferências |
| `a7d2f5b84e69` | 9 | cartões, compras, pagamentos de fatura |
| `b8e3a6c5d1f7` | 10 | `accounts.opening_balance`, `categories.dre_group` |
| `c9f4b7a2e6d1` | 11 | valor `LOAN`, dívidas, parcelas, amortizações; `commitments.debt_id`; baixa pode ser só transferência |
| `d1a8e5c3b7f2` | 12 | bens e avaliações |
| `e2b9c6d4a8f3` | 13 | valor `INVESTMENT`, investimentos, cotações, registro de requisições |
| `f3c1d7a9b5e2` | 14 | `categories.ir_kind`, informes e dependentes do IR |
| `g4d2e8b6c1a3` | 15 | apólices e plano de aposentadoria |

- Todas foram verificadas com `upgrade → check → downgrade → upgrade → check` no banco local, e `backend/tests/test_migrations.py` aplica todas num banco vazio e grava uma conta de cada tipo (pega erro de caixa de enum, que `create_all` não pega).
- **Valores de enum não saem no `downgrade`** (`LOAN`, `INVESTMENT` ficam).
- As migrações **rodam na subida do container** (`alembic upgrade head && exec uvicorn ...` no `Dockerfile`); seguro só com **no máximo 1 réplica**.
- Armadilhas antigas de Alembic: autogenerate reusa enum já criado e quebra (`type already exists`) — usar `postgresql.ENUM(..., create_type=False)`; `add_column` de enum novo precisa criar o tipo antes; sempre nomear FKs à mão.

---

## 9. Como rodar localmente (Windows, PowerShell)

- **Docker Desktop precisa estar aberto** (testes usam Testcontainers e o banco local roda em Docker). Abrir: `C:\Users\julia.jesus\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe`.
- **Cuidado crítico**: `backend/.env` aponta para o banco do **Azure**. Para qualquer execução local, **sobrescreva**:
  ```powershell
  $env:DATABASE_URL="postgresql+psycopg://cashtrail:cashtrail@localhost:5544/cashtrail"
  ```
  (usuário e senha `cashtrail` do `docker-compose.yml`; Postgres local em `localhost:5544`).
- **Portas** (nesta máquina havia conflitos: Postgres nativo do Windows em 5432/5433, porta 8000 reservada pelo Windows, 8001 e 8010 ocupadas por containers de outros projetos dela). Por isso: Postgres local **5544**, backend de desenvolvimento em **8020**, frontend em **3000**. Em outra máquina, **confira com `netstat -ano`** antes de assumir os mesmos conflitos.
- **Sempre `localhost`, nunca `127.0.0.1`** entre frontend e backend (o cookie de refresh é `SameSite=strict`).
- **Não use `uvicorn --reload`** (processos órfãos seguram a porta).
- Frontend apontando para o backend local: `$env:NEXT_PUBLIC_API_URL="http://localhost:8020"; npm run build` (o export estático embute a URL no build).
- Máquina com pouca RAM: `argon2` ("Memory allocation error") e `next build` podem falhar por memória; **repetir resolve**.
- Exemplo de subida: `docker compose up -d db`, migrar, `python -m uvicorn src.main:app --port 8020`, servir `frontend/out` com `scripts/e2e/static_server.py out 3000`.

---

## 10. Como testar

- **Backend**: `cd backend; .\.venv\Scripts\python.exe -m pytest -q` (cerca de 3 a 4 minutos; Docker aberto). `unset`/não definir `DATABASE_URL` para os testes (eles criam um Postgres próprio).
- **Frontend**: `npm run lint`, `npx tsc --noEmit`, `npm run build` (na pasta `frontend`).
- **CI**: `.github/workflows/ci.yml` roda `pytest`, `lint` e `build` (também é chamado pelo deploy).
- **Navegador (Playwright)**: roteiros em `scripts/e2e/` (ver o README lá). Cada marco de 8 a 15 tem o seu. Servem para provar a tela com números conferidos à mão; **não** fazem parte do CI.
- **Padrões de teste usados**: data fixa `TODAY = date(2026, 8, 20)` nos testes de fluxo de caixa; testes de propriedade (somas, saldo nunca negativo, aporte calculado alcança a meta); `begin_nested()` para testes de `IntegrityError`; provedores externos **sempre falsos** (nenhum teste chama a rede); limite de login e agendador **desligados** nos testes (`limiter.enabled = False`, `ENABLE_SCHEDULER=false`).

---

## 11. Azure: recursos, pipelines e armadilhas

**Recursos (assinatura Azure for Students, região Brazil South):**

| Recurso | Nome |
|---|---|
| Resource group | `cashtrail-rg` |
| PostgreSQL Flexible Server | `cashtrail-db-16143` (B1ms, 1 vCore, 2 GiB, 32 GiB, **versão 16.15**, usuário `cashtrail`, banco `cashtrail`, acesso público aberto por simplicidade do MVP) |
| Key Vault | `cashtrail-kv-7290` (modo RBAC) |
| Container Registry | `acrcashtrail` (Basic; usuário admin habilitado para o login por Secrets) |
| Container Apps Environment | `cashtrail-env` (tipo **Express**) |
| Container App backend | `cashtrail-backend` (porta 8000) |
| Container App frontend | `cashtrail-frontend` (nginx, porta 80) — URL: `https://cashtrail-frontend.ashydune-a5fddf60.brazilsouth.azurecontainerapps.io` |
| Outro grupo na mesma assinatura | `rg-mass-message-test` (não é do CashTrail; R$ 12,61 de custo acumulado; apagar se não usa mais) |

**Variáveis do backend que existem hoje:** `DATABASE_URL`, `JWT_SECRET_KEY`, `COOKIE_SECURE`, `CORS_ALLOWED_ORIGINS` (JSON válido), `ENABLE_SCHEDULER`, `APP_VERSION`. O deploy define `FRONTEND_URL`, `APP_VERSION`, `ENABLE_SCHEDULER` e, se houver secrets, e-mail ACS e `BRAPI_TOKEN`.

**Workflows (`.github/workflows/`):**
- `ci.yml`: backend (pytest) + frontend (lint e build).
- `deploy.yml`: **manual** (`workflow_dispatch`), chama o CI, liga o Postgres se estiver parado, `az acr build` das duas imagens (tag = SHA do commit), `az containerapp update` do backend, espera o `/health` devolver o SHA do deploy, builda o frontend com `NEXT_PUBLIC_API_URL` do FQDN real do backend e atualiza o frontend.
- `db-lifecycle.yml`: liga o banco (3 tentativas: **03:17, 06:17 e 09:17 UTC**) e desliga às **23:17 UTC**, todo dia (também `workflow_dispatch` com `start`/`stop`). Confere o estado antes porque `start`/`stop` falham se já estiver no estado pedido, o que torna as tentativas extras inofensivas. Os horários são adiantados porque o GitHub rodou os agendamentos com **4 a 7 horas de atraso** (medido de 2026-10-02 a 2026-10-22); se o atraso sumir, o banco desliga às 20:17 em Brasília (ligar à mão).
- Login no Azure por **OIDC**: secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` como **Repository secrets** (não só de environment, senão o db-lifecycle enxerga vazio). Credenciais federadas: `environment:production` (deploy) e `ref:refs/heads/main` (db-lifecycle).
- Secrets **opcionais** do deploy: `ACS_CONNECTION_STRING` + `EMAIL_SENDER_ADDRESS` (e-mail) e `BRAPI_TOKEN` (cotações).

**Armadilhas já enfrentadas (não repetir):**
- **Ambiente Express**: não aceita identidade gerenciada para puxar do ACR (usar autenticação por **Secrets**), não aceita `--revision-suffix` nem preenche `latestReadyRevisionName`. A prova de que a versão nova subiu é o `/health` devolver o SHA.
- **CORS**: `CORS_ALLOWED_ORIGINS` precisa ser JSON válido, senão o app cai na subida e o portal mostra "Scaled to 0" (parece ocioso, mas está em crash loop; olhe o Log stream).
- **CPU/memória** só aceitam pares válidos do plano de consumo (0.25/0.5Gi, 0.5/1.0Gi, ...).
- Static Web Apps está **bloqueado por política** na assinatura (`RequestDisallowedByAzure`); outros tipos de recurso podem ter o mesmo bloqueio.
- A senha do Postgres foi redefinida uma vez para um valor alfanumérico; ela é a única que sabe; não está em lugar nenhum do repositório (e o `backend/.env` local a contém: nunca commitar).
- Postgres: `ALTER TYPE ... ADD VALUE` das migrações roda em modo autocommit; a versão 16.15 do Azure é compatível com o que foi testado.
- Cookie de refresh `SameSite=strict`: em produção funciona porque os dois Container Apps estão sob `azurecontainerapps.io`.

---

## 12. Onde paramos na sessão de Azure (ponto exato)

**Decisões fechadas em 2026-10-15** (também no doc 31): D1 banco 06h–23h; D2 criar o ACS do zero na mesma sessão; D3 deploy sem token da brapi; D4 publicar com a UI atual; D5 dados são de teste.

**Atualização de 2026-10-22:** o **Deploy já foi feito** (2026-10-15 18:56 UTC, commit `bbe1b52`, `/health` confirma). `push` e CI verdes. O ACS ainda **não** existe (só há os 3 secrets do OIDC no repositório). Descoberto que o agendamento do banco atrasava de 4 a 7 horas no GitHub (na prática ficava ligado de ~11h20 a ~03h55 em Brasília); a Julia escolheu adiantar os crons e tirá-los da hora cheia (seção 11). Ainda em 2026-10-22: **ACS criado** (`cashtrail-email` + `cashtrail-comm`, domínio gratuito do Azure), secrets `ACS_CONNECTION_STRING` e `EMAIL_SENDER_ADDRESS` no GitHub, **novo Deploy** (`acc0956`, `/health` confirma) e **"Esqueci a senha" testado em produção pela Julia: o e-mail chegou e a troca de senha funcionou** (o backend `acs` não precisou de ajuste). **Roteiro de fumaça (2026-10-22, em produção, usuários de teste `...@example.com`):** os 8 roteiros de `scripts/e2e/` passaram (Marcos 8 a 15, com brapi e Banco Central reais), mais importação de extrato (amostra sintética: 6 linhas, reimportação marca 6/6 duplicadas) e CSVs de DRE, fluxo, patrimônio e IR. Achado: o **"período anterior" do DRE** usa o mesmo número de dias, então outubro (31 dias) é comparado com **31/08 a 30/09**, e não com setembro (o doc 25 promete "comparado com o mês anterior"); aguardando decisão da Julia. Pendente só com ela: conferir os dados antigos da conta dela, o cartão real, o programa da Receita e um extrato real.

**Passo 0 (código na `main`)**: feito.

**Passo A (conferências no portal) — feito, resultados:**
- PostgreSQL **16.15**, estado **Stopped**, Burstable B1ms.
- **Backup (R-009)**: retenção de **7 dias** (padrão); há "Automated backup #1" concluído em 2026-10-12, retido até 2026-10-19. **R-009 fechado.**
- Variáveis do backend presentes (lista acima). O estado do Container App aparecia como "stopped" (escalado a zero).
- Custo (Azure): **Container Registry R$ 25,22** acumulado (maior despesa), **PostgreSQL R$ 0,00** (quase não ficou ligado), previsão do período **R$ 54,62**, e **R$ 12,61** no grupo `rg-mass-message-test`.

**Alerta de custo aberto (decisão pendente dela):** ligar o banco ~17h/dia custa, pela estimativa do doc 06 (~US$ 12/mês ligado 24h), perto de **US$ 8,5/mês só de compute** — **estimativa**, não preço verificado. Somado ao Registry, o ano pode **passar dos US$ 100 de crédito** do Azure for Students. Opções que apresentei: (1) manter a janela e acompanhar o Cost Management uma semana depois do deploy; (2) janela menor (ex.: 09:00 às 20:00 Brasília, ~11h/dia); (3) voltar a ligar só às segundas. **Ela ainda não escolheu.**

**Ainda sem resposta dela:** mínimo e máximo de réplicas do backend (precisa ser máx. 1); a tag mais recente da imagem em `acrcashtrail → Repositories → cashtrail-backend` (ponto de volta do rollback); quanto resta do crédito.

**Passo B — criar o ACS (pendente, ela ia fazer no portal):**
1. Registrar o provedor `Microsoft.Communication` (Subscriptions → Resource providers).
2. Criar **Email Communication Services** (`cashtrail-email`, grupo `cashtrail-rg`, data location Brasil).
3. Adicionar o **domínio gratuito do Azure** (Azure subdomain / 1-click add) e esperar provisionar.
4. Criar **Communication Services** (`cashtrail-comm`, mesma data location).
5. Em `cashtrail-comm`: Email → Domains → **Connect domain**.
6. Anotar o remetente (`DoNotReply@<id>.azurecomm.net`, em MailFrom addresses).
7. Pegar a **connection string** (Settings → Keys).
8. No GitHub (Settings → Secrets and variables → Actions → **Repository secrets**): `ACS_CONNECTION_STRING` e `EMAIL_SENDER_ADDRESS`. **Nunca colar a connection string no chat.**

**Depois do ACS (ordem do doc 31, seção 9):** confirmar que o CI da `main` está verde → *Actions → Deploy → Run workflow* → acompanhar o passo "Wait for new backend version to be live" → rodar o **roteiro de fumaça de 14 passos** (doc 31, seção 10) na URL pública → se falhar, plano de reversão (doc 31, seção 11: voltar a imagem anterior do ACR; restaurar o backup em último caso; evitar `alembic downgrade` em produção).

**Observações do primeiro envio de e-mail real**: o código do backend `acs` nunca foi testado contra o Azure de verdade; pode precisar de um ajuste pequeno no primeiro envio.

---

## 13. Pendências e backlog

**Bloqueiam ou afetam o deploy**
- Escolher a janela do banco diante do custo (seção 12).
- Passo B (ACS) e depois o Deploy e o roteiro de fumaça.
- Confirmar réplicas (máx. 1) e anotar a tag de rollback.

**Não bloqueiam**
- **Redesign visual e menu**: o menu já tem ~20 itens e quebra em duas linhas. Pesquisa em `docs/planning/21-ui-research.md`; ela rejeitou 4 paletas genéricas e quer algo **autêntico**; falta ela mandar **capturas de ERPs/apps de referência** (por anexo no chat ou pasta). Próximo round deve ser **orientado a conceito**, não variação de paleta.
- **Termos de uso da brapi** e criação do token `BRAPI_TOKEN` (hoje sem token só PETR4, VALE3, MGLU3 e ITUB4 são cotados).
- **Extrato real** de banco para validar o parser de CSV (hoje só amostras sintéticas, em `docs/exemplos/extrato-exemplo.csv`) e o **banco/fechamento/vencimento do cartão real** para validar a regra de fatura.
- Trocar o e-mail de ACS por SMTP antes de 2028-09-30 (o adaptador em `core/email.py` é plugável).
- **Atualização anual do IR**: criar `backend/src/features/tax/parameters/<ano>.json` a cada ano-calendário a partir da página oficial de tabelas da Receita.
- Cotação automática do Tesouro Direto, TWR/XIRR, desdobramentos automáticos, day trade/ETF/BDR/cripto no IR, alertas por e-mail (renovação de seguro, DARF), monitoramento de produção, Key Vault com referência viva.
- Apagar as branches locais antigas e o grupo `rg-mass-message-test` se não for mais usado.

---

## 14. Verificações oficiais ainda abertas (aparecem na tela de IR como "premissas não verificadas")

- 20% do **desconto simplificado** (a Receita publica só o limite de R$ 17.640,00).
- **Base do redutor** da Lei 15.270/2025 (assumi o total dos rendimentos tributáveis; o redutor é zero em R$ 88.200).
- **FII a 20%**, compensação de prejuízo por modalidade, **DARF mínimo de R$ 10,00** e aplicação do **IRRF de 0,005%** a FIIs.
- **PLR**: as fontes divergem na faixa isenta (R$ 7.640,80 × R$ 8.214,40); o sistema usa o valor do informe.
- ETF, BDR, cripto e fundos **não são apurados**; day trade só é **sinalizado**.
- Tabela e deduções do ano-calendário 2026 vêm da página oficial de tabelas da Receita (seção "a partir do exercício 2027"); podem mudar por norma posterior.

---

## 15. Fontes externas verificadas

- **Banco Central (SGS)**, sem autenticação: CDI diário série **12**, IPCA mensal série **433**; consulta exige datas e limita a 10 anos por janela (o provedor divide em janelas). Verificado com chamadas reais.
- **brapi.dev** (plano grátis): 15.000 requisições/mês, 1 ativo por requisição, atraso de 30 min, histórico de 3 meses; `GET /api/quote/PETR4` funciona sem token (sandbox lista PETR4, VALE3, MGLU3, ITUB4); outros ativos aparentemente exigem token (não confirmado). Termos de uso para uso pessoal **não lidos**.
- **Tesouro Direto**: CSV oficial de histórico (centenas de MB, sem o valor do dia); sem cotação automática na v1.
- **ACS Email**: aposentadoria em **2028-09-30** (guia oficial de retirada da Microsoft).
- **Receita Federal**: tabelas, deduções, redutor, regras de renda variável em ações (15%, isenção de R$ 20.000/mês de vendas, DARF 6015, prazo no último dia útil do mês seguinte), saúde sem limite, PGBL até 12%, PGBL × VGBL e tabela regressiva (35% a 10%), via páginas oficiais.

---

## 16. Gotchas técnicos acumulados

- **Base UI Select**: exige `items` (`{value,label}[]`); sem isso o gatilho mostra o valor cru até abrir. `onValueChange` pode passar `null`.
- **Lint do React**: regra contra `setState` direto em efeito — carregar dados com `.then` e flag `cancelled`, usar `useWatch` em vez de `watch`, e `reloadKey` para recarregar.
- **`create_transaction(commit=False)`**, `create_commitment(commit=False)`, `cancel_commitment(commit=False)` e `transfers.create_transfer(commit=False)` existem para uma slice compor várias criações numa **única transação**.
- **Rate limit de login (5/min)**: rodar vários roteiros de navegador seguidos pode dar `429`; esperar 1 minuto.
- **`next build`** pode estourar memória; repetir.
- **`localhost` vs `127.0.0.1`**: sempre `localhost` (cookie `SameSite=strict`). Outras aplicações locais dela podem ocupar 8001/8010; conferir a lista de rotas (`/openapi.json`), não só `/health`.
- Heredocs do shell do assistente falham com certos caracteres; arquivos grandes são escritos pela ferramenta de escrita.
- O agendador em produção só existe enquanto o container está de pé (escala a zero): por isso recorrências e cotações também rodam **na subida** (cotações em segundo plano, pulando cotação com menos de 4h) e o botão "Atualizar cotações" é o caminho confiável.
- CSV exportado: UTF-8 com BOM, separador `;`, vírgula decimal; células de **texto** que começam com `= + - @ tab CR` ganham `'` na frente (proteção contra injeção de fórmula); números não.

---

## 17. Mapa de `docs/planning/`

`00-project-brief`, `01-discovery`, `02-market-research`, `03-requirements`, `04-usecases`, `05-integrations`, `06-costs`, `07-stack`, `08-architecture`, `09-vertical-slices`, `10-data-model`, `11-security`, `12-mvp`, `13-roadmap`, `14-estimates`, `15-risks`, `17-traceability`, `18-backlog`, `19-definition-ready-done`, `20-gates-checkpoint`, `21-ui-research`, `22-erp-pessoal-discovery`, `23-marco-8-contas-a-pagar-receber`, `24-marco-9-cartoes-e-faturas`, `25-marco-10-fluxo-de-caixa-e-dre`, `26-marco-11-dividas-e-financiamentos`, `27-marco-12-patrimonio-e-balanco`, `28-marco-13-investimentos`, `29-marco-14-irpf`, `30-marco-15-seguros-e-aposentadoria`, `31-checklist-pre-deploy`, e `decisions/ADR-001..007`.

Cada doc de marco (23 a 30) tem: objetivo e critério de saída, o que já existia no código, pesquisa com fontes, escopo, requisitos (RF) e regras de negócio (RB), decisões no formato DECISÃO/ALTERNATIVAS/TRADE-OFFS, modelo de dados, plano de implementação, riscos e, no fim, o **STATUS** com o que foi implementado e as "decisões tomadas ao codar".

Numeração de requisitos: RF-001 a RF-075 e RB-001 a RB-048 (ver os docs de cada marco para o significado).

---

## 18. Índice da memória do assistente (cópia fiel do `MEMORY.md` local)

- Fluxo "descoberta primeiro": prompt permanente dela; nada de código antes de fases e gates; formato DECISÃO/ALTERNATIVAS/TRADE-OFFS; sinalizar o conflito AWS × Azure.
- Git: nunca commitar nem dar push por ela, em qualquer repositório, sempre.
- Branch por fase: criar a branch antes de cada marco (criar é permitido; commit e push são dela).
- Pesquisa de UI: a interface precisa nascer de pesquisa profunda de apps financeiros parecidos, não do visual padrão do shadcn; round 1 de 4 paletas foi rejeitado por ser genérico.
- Visão geral do CashTrail: a descoberta completa mora em `docs/planning/` do repositório.
- Deploy em lote: ela não quer deploy por marco; só quando ela pedir.
- Status por marco: Marco 2 (deploy inicial e armadilhas do Azure), Marcos 3 a 6 (MVP, implantado em 2026-09-28), Marco 7 em diante (registro corrido até o Marco 15, incluindo as decisões de deploy de 2026-10-15).

---

## 19. Próximos passos recomendados (em ordem)

1. Confirmar `git push origin main` e o CI verde; commitar este documento e `scripts/e2e/`.
2. Decidir a janela do banco diante do custo (seção 12) e, se mudar, ajustar os crons do `db-lifecycle.yml`.
3. Responder as pendências do passo A (réplicas, tag de rollback, crédito restante).
4. Criar o ACS (passo B) e colocar os 2 secrets no GitHub.
5. Rodar o **Deploy**, acompanhar o `/health` e executar o roteiro de fumaça.
6. Depois do deploy: atualizar o `README` (status e link), acompanhar o custo por uma semana e só então começar o **redesign** (pedir as capturas de ERPs a ela primeiro).
