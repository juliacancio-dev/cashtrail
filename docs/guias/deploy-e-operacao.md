# Deploy e operação

Como publicar uma versão, conferir que subiu, voltar atrás e manter a produção. O deploy é **manual e em lote**: vários marcos de uma vez, quando a mantenedora decide, nunca automático a cada push.

## Infraestrutura

Assinatura Azure for Students, região Brazil South, grupo de recursos `cashtrail-rg`.

| Recurso | Nome | Configuração |
|---|---|---|
| PostgreSQL Flexible Server | `cashtrail-db-16143` | Burstable B1ms, versão 16, banco e usuário `cashtrail`, backup automático de 7 dias, acesso público com senha |
| Container Registry | `acrcashtrail` | Basic, usuário admin habilitado (o ambiente Express não aceita identidade gerenciada para puxar imagens) |
| Container Apps Environment | `cashtrail-env` | tipo **Express** |
| Container App | `cashtrail-backend` | porta 8000, **réplicas: mínimo 0, máximo 1** ([ADR-018](../decisoes/ADR-018-migracoes-na-subida.md)) |
| Container App | `cashtrail-frontend` | nginx, porta 80 |
| Key Vault | `cashtrail-kv-7290` | modo RBAC; ainda sem referência viva no Container App |
| Communication Services | `cashtrail-comm` + `cashtrail-email` | e-mail com domínio gratuito do Azure ([ADR-017](../decisoes/ADR-017-email-azure-communication-services.md)) |

URL pública: <https://cashtrail-frontend.ashydune-a5fddf60.brazilsouth.azurecontainerapps.io>

## Workflows

| Workflow | Gatilho | O que faz |
|---|---|---|
| [`ci.yml`](../../.github/workflows/ci.yml) | push e pull request | `pytest` do backend; `lint` e `build` do frontend |
| [`deploy.yml`](../../.github/workflows/deploy.yml) | manual (`workflow_dispatch`) | roda o CI; liga o banco se estiver parado; `az acr build` das duas imagens com tag = SHA; atualiza o backend; espera o `/health` devolver o SHA; builda o frontend com a URL real do backend; atualiza o frontend |
| [`db-lifecycle.yml`](../../.github/workflows/db-lifecycle.yml) | agenda diária e manual (`start`/`stop`) | liga e desliga o PostgreSQL |

### Secrets do GitHub

Todos como **Repository secrets** (secrets só de *environment* ficam vazios para o `db-lifecycle`).

| Secret | Obrigatório | Uso |
|---|---|---|
| `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` | sim | login OIDC; credenciais federadas para `environment:production` (deploy) e `ref:refs/heads/main` (agenda do banco) |
| `ACS_CONNECTION_STRING`, `EMAIL_SENDER_ADDRESS` | não | e-mail real; sem eles o link de recuperação só aparece no log |
| `BRAPI_TOKEN` | não | cotações além dos ativos de teste |

### Variáveis do backend em produção

Criadas à mão no Container App (o deploy não as apaga): `DATABASE_URL` e `JWT_SECRET_KEY` (como *secrets*), `COOKIE_SECURE=true` e `CORS_ALLOWED_ORIGINS` (**JSON válido**, por exemplo `["https://cashtrail-frontend..."]`). O deploy define `APP_VERSION`, `FRONTEND_URL`, `ENABLE_SCHEDULER=true` e, se houver secrets, o e-mail e o `BRAPI_TOKEN`. A lista completa de variáveis está no [README do backend](../../backend/README.md#configuração).

## Publicar uma versão

1. **Antes:** a `main` contém tudo o que vai subir e o CI dela está verde. Liste as migrações novas desde o último deploy ([modelo de dados](../arquitetura/modelo-de-dados.md#migrações)) e leia cada uma procurando o que altera tabela existente.
2. Confira no portal que o backup automático existe e que o backend continua com **máximo 1 réplica**.
3. Anote a tag (SHA) da imagem atual do backend em `acrcashtrail → Repositories → cashtrail-backend`: é o ponto de volta.
4. **GitHub → Actions → Deploy → Run workflow** na `main`.
5. Acompanhe o passo *Wait for new backend version to be live*: ele só passa quando o `/health` devolve o SHA do commit.
6. Rode o roteiro de fumaça abaixo na URL pública.
7. Registre a versão no [CHANGELOG](../../CHANGELOG.md).

### Roteiro de fumaça (15 minutos)

1. `GET /health` mostra o SHA do deploy.
2. Entrar com uma conta existente; contas, lançamentos e orçamentos antigos continuam lá.
3. Calendário abre no mês atual; o saldo de hoje bate com a soma das contas em Contas.
4. Criar uma conta a pagar, pagar e desfazer.
5. Lançar uma compra no cartão e ver a fatura.
6. Abrir DRE, Fluxo de caixa e Balanço; exportar um CSV e abrir no Excel.
7. Investimentos: **Atualizar cotações**.
8. "Esqueci a senha": o e-mail chega e a troca funciona.
9. Tema claro e escuro; abrir a gaveta de navegação no celular.

Os roteiros de `scripts/e2e/` também rodam contra a produção (`E2E_API` e `E2E_WEB`); veja o [README deles](../../scripts/e2e/README.md#contra-a-produção). Use usuários `...@example.com`.

## Voltar atrás

| Situação | Ação |
|---|---|
| Migração falhou e o app não sobe | O banco fica na revisão anterior (o Alembic roda em transação, exceto `ADD VALUE`). Volte a imagem: `az containerapp update -n cashtrail-backend -g cashtrail-rg --image acrcashtrail.azurecr.io/cashtrail-backend:<sha-anterior>` |
| Migrações aplicaram, mas o código novo tem bug grave | Prefira **corrigir para a frente**. Voltar a imagem é seguro só se o código antigo não depender do que mudou; tabelas e colunas novas não atrapalham o código antigo |
| Dado corrompido | Restaurar o backup para um servidor novo e apontar `DATABASE_URL` para ele |

**Evite `alembic downgrade` em produção**: ele apaga tabelas novas e baixas só com transferência. Só com backup em mãos.

## Agenda do banco

O PostgreSQL fica ligado das **06h às 23h (Brasília)**, todos os dias. Fora dessa janela a demonstração não responde; para usar, rode *Actions → DB lifecycle → Run workflow → start*.

O `db-lifecycle.yml` tenta ligar às 03:17, 06:17 e 09:17 UTC e desliga às 23:17 UTC. Os horários são adiantados e fora da hora cheia porque o GitHub rodou os agendamentos com **4 a 7 horas de atraso** (medido de 2026-10-02 a 2026-10-22); o workflow confere o estado antes, então as tentativas extras são inofensivas. **Se o atraso sumir**, o banco desliga às 20:17 em Brasília; ajuste os horários.

## Custo

| Item | Observação |
|---|---|
| Container Registry | maior despesa fixa (cobrado por dia) |
| PostgreSQL | só cobra compute ligado; ~17 h por dia é uma **estimativa** de US$ 8,50/mês (a partir de ~US$ 12/mês ligado 24 h, pesquisa de 2026-09, não verificado na fatura) |
| Container Apps | escala a zero; dentro da cota gratuita no uso atual |

Acompanhe em **Cost Management** e compare com o crédito restante do Azure for Students. Se o ano passar do crédito, as alavancas são encurtar a janela do banco ou trocar o Registry.

## Armadilhas do Azure

- **"Scaled to 0" com o app quebrado.** O portal mostra o app ocioso quando ele está em *crash loop*. Olhe o **Log stream**. Causa mais comum: `CORS_ALLOWED_ORIGINS` que não é JSON válido.
- **Ambiente Express** não aceita `--revision-suffix` nem preenche `latestReadyRevisionName`; a prova de que a versão nova subiu é o `/health` com o SHA.
- **CPU e memória** só aceitam pares válidos do plano de consumo (0.25/0.5Gi, 0.5/1.0Gi...).
- **Políticas da assinatura** bloqueiam alguns tipos de recurso (`RequestDisallowedByAzure`), como o Static Web Apps.
- **Agendador e escala a zero:** os jobs só rodam com o container de pé; por isso recorrências e cotações também rodam na subida. O botão "Atualizar cotações" é o caminho confiável.
- **Rate limit** é por instância; continua correto com uma réplica.
