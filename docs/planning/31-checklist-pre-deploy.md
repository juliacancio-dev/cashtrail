# CashTrail — Checklist de pré-deploy (Marcos 7 a 15)

> Consolida o que falta para publicar tudo de uma vez, numa única sessão de Azure, quando a Julia decidir. **Nada aqui foi executado**: nenhum recurso do Azure foi tocado e nenhum deploy foi disparado. Escrito em 2026-10-15, com o código da branch `marco-15-seguros-e-aposentadoria`.

Legenda: **FATO** (verificado no código ou nos arquivos) · **INFERÊNCIA** · **DESCONHECIDO** (precisa de conferência no portal ou fonte oficial).

## 1. Estado do código

- **FATO:** a `main` está no commit `f1344ab` (Marco 7). Os Marcos 8 a 15 estão em branches **lineares**: a `marco-15-seguros-e-aposentadoria` tem 10 commits à frente da `main` e a `main` não tem nada que ela não tenha, então o merge pode ser **fast-forward**.
- **FATO:** 734 testes passando, `lint` do frontend e `alembic check` limpos, **8 migrações novas** desde o último deploy real.
- **FATO:** o que está em produção hoje é o **MVP dos Marcos 1 a 6** (deploy de 2026-09-28). Tudo dos Marcos 7 a 15 é novo para produção.
- **Para a Julia (não faço commit nem push):**
  ```
  git switch main
  git merge --ff-only marco-15-seguros-e-aposentadoria
  git push origin main
  ```
  O deploy é **manual** (`Actions → Deploy → Run workflow`); empurrar para a `main` só roda o CI.

## 2. Decisões que só a Julia pode tomar

| # | Decisão | Por que importa | Recomendação |
|---|---|---|---|
| D1 | **Agenda do banco**: hoje o `db-lifecycle.yml` desliga o Postgres toda noite (03:00 UTC) e **só liga às segundas** (06:00 UTC) | **FATO:** de terça a domingo o app não funciona, a menos que alguém ligue o banco à mão. Com o ERP completo isso atrapalha o uso diário | Ligar todo dia útil de manhã (um segundo `cron`) ou aceitar o custo do banco 24/7; decidir com o custo à vista (doc 06) |
| D2 | **E-mail de recuperação de senha**: ACS (decisão dela de 2026-10-08, serviço **aposentado em 2028-09-30**) ou seguir sem e-mail (link só no log) | Sem e-mail, "esqueci a senha" só funciona com acesso ao log do Container App | Seguir a decisão anterior (ACS) e tratar a troca por SMTP como item futuro; é opcional para o deploy |
| D3 | **Cotações automáticas** (brapi): criar token e ler os termos de uso | **DESCONHECIDO:** termos de uso para uso pessoal não lidos; sem token só PETR4, VALE3, MGLU3 e ITUB4 funcionam | Deploy **sem** token primeiro (valor manual funciona); criar o token depois de ler os termos |
| D4 | **Visual**: publicar com a interface funcional atual ou esperar o redesign | O menu já tem ~20 itens e quebra em duas linhas; a pesquisa visual (doc 21) segue sem decisão e sem as capturas de ERPs | Publicar agora é possível; o redesign não bloqueia nada técnico |
| D5 | **Dados de produção**: o MVP em produção tem dados reais dela? | Define o quanto o backup e o rollback pesam | Tratar como dados reais e fazer backup antes (item B1) |

## 3. Bloqueadores técnicos (fazer antes de rodar o Deploy)

| ID | Item | Estado | Como fechar |
|---|---|---|---|
| B1 | **Backup do Postgres (R-009)**: retenção e restauração nunca confirmadas | Aberto desde o MVP | Portal → `cashtrail-db-16143` → *Backup and restore*: anotar a retenção e, **antes do deploy**, fazer um backup/restauração de teste ou um `pg_dump` |
| B2 | **Versão do PostgreSQL no Azure** | **DESCONHECIDO** | Portal → *Overview*. As migrações usam `ALTER TYPE ... ADD VALUE` em modo autocommit (valores `LOAN` e `INVESTMENT`); foram testadas em Postgres 16 |
| B3 | **Variáveis já existentes no Container App** | Provavelmente ok | **FATO:** `DATABASE_URL`, `JWT_SECRET_KEY`, `COOKIE_SECURE=true` e `CORS_ALLOWED_ORIGINS` (JSON) foram criadas à mão na Marco 2 e o `--set-env-vars` do deploy **não** as apaga. Conferir no portal que continuam lá |
| B4 | **Réplicas**: as migrações rodam na subida do container | **FATO:** seguro só com **no máximo 1 réplica** | Conferir *Scale* = min 0 / max 1 |
| B5 | **Banco ligado** durante o deploy | **FATO:** o `deploy.yml` já liga o Postgres se estiver parado | Nada a fazer; só saber que o primeiro start pode levar minutos |
| B6 | **Secrets do GitHub** | **FATO:** login OIDC já configurado (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`) | Opcionais: `ACS_CONNECTION_STRING` + `EMAIL_SENDER_ADDRESS` (D2) e `BRAPI_TOKEN` (D3, já tratado no `deploy.yml`) |

## 4. Migrações que vão rodar na subida (em ordem)

| Revisão | Marco | O que faz | Observação de risco |
|---|---|---|---|
| `a1c9e4d27f10` | 7 | tokens de recuperação de senha, `users.password_changed_at` | tabela nova |
| `c3e8b1f05a92` | 7 | `statement_imports` | tabela nova |
| `d4a7c2e91b36` | 8 | `commitments`, `commitment_settlements` | tabelas novas (+ enum `commitment_direction`) |
| `e5b8d3f02c47` | 8 | `recurring_transactions.generate_as_commitment`, vínculo com compromissos | coluna com padrão |
| `f6c9e4a13d58` | 9 | `transfers` | tabela nova |
| `a7d2f5b84e69` | 9 | `credit_cards`, `card_purchases`, `card_invoice_payments` | tabelas novas |
| `b8e3a6c5d1f7` | 10 | `accounts.opening_balance` (padrão 0), `categories.dre_group` | colunas em tabelas existentes, **preenchidas com padrão** |
| `c9f4b7a2e6d1` | 11 | `ADD VALUE 'LOAN'`; `debts*`; `commitments.debt_id`; `commitment_settlements.transaction_id` passa a **aceitar nulo** | **altera tabela existente**; o `downgrade` apaga baixas só-transferência |
| `d1a8e5c3b7f2` | 12 | `assets`, `asset_valuations` | tabelas novas |
| `e2b9c6d4a8f3` | 13 | `ADD VALUE 'INVESTMENT'`; `investment_*`, `quote_request_log` | tabelas novas |
| `f3c1d7a9b5e2` | 14 | `categories.ir_kind`, `tax_year_settings`, `tax_income_statements` | coluna nula em tabela existente |
| `g4d2e8b6c1a3` | 15 | `insurance_policies`, `retirement_plans` | tabelas novas |

- **FATO:** cada migração foi aplicada em `upgrade → check → downgrade → upgrade → check` no banco local, e o teste `tests/test_migrations.py` aplica **todas** num banco vazio e grava uma conta de cada tipo.
- **FATO:** valores de enum **não saem** no `downgrade`: `LOAN` e `INVESTMENT` ficam no tipo `account_type` mesmo voltando a migração (inofensivo).
- **INFERÊNCIA:** nenhuma migração apaga ou reescreve dados existentes; o risco real é uma migração falhar no meio. Como o Alembic roda em transação (exceto o `ADD VALUE`), a falha deixa o banco na revisão anterior, e o container não sobe (o `/health` nunca devolve o SHA novo e o deploy falha com mensagem clara).
- **Não testado:** aplicar as 12 migrações sobre um banco **com dados de produção**. O mais próximo é restaurar o backup (B1) num banco temporário e rodar `alembic upgrade head` contra ele antes do deploy real.

## 5. Variáveis de ambiente do backend

| Variável | Onde | Obrigatória | Observação |
|---|---|---|---|
| `DATABASE_URL`, `JWT_SECRET_KEY` | Container App (secret) | sim | já existem (B3) |
| `COOKIE_SECURE=true`, `CORS_ALLOWED_ORIGINS` | Container App | sim | JSON válido, ex.: `["https://..."]` |
| `ENABLE_SCHEDULER=true` | `deploy.yml` define | sim | liga as 3 tarefas: recorrências, cotações na subida e a cada 24h |
| `APP_VERSION`, `FRONTEND_URL` | `deploy.yml` define | sim | usados pelo `/health` e pelo link do e-mail |
| `EMAIL_BACKEND=acs`, `ACS_CONNECTION_STRING`, `EMAIL_SENDER_ADDRESS` | `deploy.yml` (se houver secrets) | não | D2; sem eles o link só aparece no log |
| `BRAPI_TOKEN` | `deploy.yml` (se houver secret) | não | D3; **nunca** vai ao frontend nem ao log (testado) |
| `QUOTES_MONTHLY_CAP` | Container App | não | padrão 10000 (o plano grátis permite 15000) |
| `BRAPI_BASE_URL` | Container App | não | padrão `https://brapi.dev` |

## 6. Comportamentos de produção que a Julia deve conhecer

- **FATO:** com **escala a zero**, o agendador só existe enquanto o container está de pé. Por isso as recorrências e as cotações também rodam **na subida** (as cotações em segundo plano, sem atrasar o `/health`, e pulando cotação com menos de 4 horas). O botão **Atualizar cotações** continua sendo o caminho confiável.
- **FATO:** limite de requisições à brapi protegido por um teto mensal (`quotes_monthly_cap`) e por um registro de cada chamada.
- **INFERÊNCIA / não verificado:** o Azure costuma **religar sozinho** um Postgres Flexible Server parado depois de alguns dias; se for o caso, o `stop` noturno cobre isso, mas o comportamento não foi conferido.
- **FATO:** limite de taxa (login 5/min) é por instância; com 1 réplica funciona.
- **FATO:** o patrimônio histórico recalcula 12 meses a cada abertura (sem snapshot). Para uso pessoal é rápido; **medir** se o histórico crescer muito.

## 7. Verificações fiscais e de fontes ainda abertas

Estas **não bloqueiam o deploy**, mas aparecem na tela de IRPF como "premissas não verificadas":

- 20% do desconto simplificado; base do redutor da Lei 15.270; 20% para FII e compensação por modalidade; DARF mínimo de R$ 10; aplicação do IRRF de 0,005% a FIIs.
- PLR: as fontes divergem na faixa isenta; o sistema usa o valor do informe.
- ETF, BDR, cripto e fundos não são apurados.
- **Anual:** criar `backend/src/features/tax/parameters/<ano>.json` a cada ano-calendário, a partir da página oficial de tabelas da Receita.
- Termos de uso da brapi (D3).

## 8. O que **nunca** foi visto por ela no navegador

- Verificado só por mim com Playwright: `/commitments` (checkbox de recorrência), `/import`, `/debts`, `/assets`, `/investments`, `/tax`, `/insurance`, `/retirement` e os cartões do dashboard.
- **DESCONHECIDO:** o parser de CSV nunca viu um extrato **real** do banco dela, e a regra de fatura nunca foi conferida com o fechamento e o vencimento do cartão **real**.
- Ao subir, vale ela clicar tudo uma vez (roteiro abaixo).

## 9. Ordem sugerida da sessão de Azure (uma só)

1. **Backup (B1)** e conferência de versão e de variáveis (B2, B3, B4).
2. *Opcional:* restaurar o backup num banco temporário e rodar `alembic upgrade head` contra ele (ensaio das migrações com dados reais).
3. Decidir D1 (agenda do banco) e ajustar o `db-lifecycle.yml` se for o caso.
4. *Opcional:* criar o ACS e os 2 secrets (D2); criar o token da brapi depois de ler os termos (D3).
5. `git merge --ff-only` e `push` na `main` (CI roda sozinho).
6. **Run workflow → Deploy.** Acompanhar o *Wait for new backend version to be live*.
7. Rodar o roteiro de fumaça (seção 10) na URL pública.
8. Se algo falhar, seção 11.

## 10. Roteiro de fumaça pós-deploy (15 minutos)

1. `GET /health` mostra o SHA do deploy.
2. Entrar com a conta existente e conferir **contas, lançamentos e orçamentos antigos** (nada se perdeu).
3. `/accounts`: editar o saldo inicial de uma conta; o saldo atual muda.
4. `/categories`: marcar o grupo de DRE e a marca fiscal de duas categorias.
5. `/commitments`: criar uma conta a pagar, pagar, desfazer.
6. `/cards`: configurar o cartão (fechamento/vencimento reais), lançar uma compra, ver a fatura **e conferir com a fatura real**.
7. `/debts`: cadastrar uma dívida de teste com simulação e pagar uma parcela; conferir o DRE do mês.
8. `/assets` e `/net-worth`: cadastrar um bem e conferir o patrimônio.
9. `/investments`: cadastrar PETR4, comprar, **Atualizar cotações**.
10. `/tax`: digitar o informe e conferir a estimativa com o programa da Receita.
11. `/insurance` e `/retirement`: cadastrar uma apólice e salvar um plano.
12. `/import`: importar um **extrato real** (primeira vez com dado real).
13. "Esqueci a senha" (se o ACS estiver ligado) ou conferir o link no log.
14. Exportar um CSV (DRE) e abrir no Excel.

## 11. Plano de reversão

| Situação | Ação |
|---|---|
| Migração falhou, o app não sobe | O banco fica na revisão anterior (transação). Reverter a imagem do Container App para a tag anterior no ACR (`az containerapp update --image .../cashtrail-backend:<sha-anterior>`); o MVP antigo volta a subir sobre o mesmo banco **só se a migração falhou antes de aplicar**. |
| Migrações aplicaram, mas o app novo tem bug grave | Preferir **corrigir para a frente**. Voltar a imagem antiga é seguro **só** para código que não depende das tabelas novas; colunas e tabelas novas não atrapalham o código antigo. |
| Dado corrompido | Restaurar o backup (B1) para um servidor novo e apontar o `DATABASE_URL` para ele. |

- **FATO:** as imagens ficam no ACR com a tag do SHA de cada deploy, então a anterior continua disponível.
- **Cuidado:** `alembic downgrade` em produção **apaga** tabelas novas e baixas só-transferência de dívida; só com backup em mãos.

## 12. Fora do escopo deste deploy (backlog)

- Redesign visual e menu lateral (doc 21, aguardando capturas de ERPs).
- Migrar o e-mail de ACS para SMTP antes de 2028-09-30.
- Cotação automática do Tesouro Direto (a fonte oficial só tem histórico em CSV grande).
- TWR/XIRR, desdobramentos automáticos, day trade, ETF/BDR/cripto no IR.
- Alertas por e-mail (renovação de seguro, DARF).
- Monitoramento/alertas de produção e Key Vault com referência viva (hoje os segredos são colados no Container App).
