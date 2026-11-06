# CashTrail

**Personal Finance Management Platform**

Uma plataforma de gestão financeira pessoal desenvolvida com foco em organização financeira, integridade dos dados, segurança e decisões de arquitetura bem fundamentadas.

O CashTrail nasceu de um processo de discovery que abrangeu o problema, a pesquisa de soluções existentes, os requisitos funcionais e não funcionais, a arquitetura, os registros de decisões técnicas (ADRs) e o planejamento de implementação.

**[Acessar demonstração](https://cashtrail-frontend.ashydune-a5fddf60.brazilsouth.azurecontainerapps.io)** · **[Explorar a documentação](docs/README.md)**

> O banco de dados fica ligado das 06h às 23h (horário de Brasília). Fora dessa janela, a demonstração não responde.

---

## Sobre o projeto

Controlar as finanças pessoais envolve mais do que registrar receitas e despesas. É necessário entender para onde o dinheiro está indo, acompanhar compromissos futuros, estabelecer metas e avaliar a evolução do patrimônio.

O CashTrail centraliza essas informações em uma aplicação que conecta movimentações financeiras, orçamento, planejamento e relatórios, preservando a consistência dos dados e evitando que a mesma movimentação seja contabilizada mais de uma vez.

O projeto também funciona como um estudo prático de engenharia de software: da investigação inicial à publicação em nuvem, com decisões arquiteturais documentadas, testes automatizados e pipeline de CI/CD.

## Estrutura do repositório

| Diretório | Conteúdo | Guia |
|---|---|---|
| [`backend/`](backend/) | API em FastAPI, organizada em vertical slices, com migrações Alembic e testes contra PostgreSQL real | [README do backend](backend/README.md) |
| [`frontend/`](frontend/) | Aplicação Next.js exportada como site estático e servida por nginx | [README do frontend](frontend/README.md) |
| [`docs/`](docs/) | Produto, arquitetura, decisões (ADRs), guias, roadmap e o desenho de cada marco | [Índice da documentação](docs/README.md) |
| [`scripts/e2e/`](scripts/e2e/) | Roteiros Playwright usados para verificar cada tela num navegador real | [README dos roteiros](scripts/e2e/README.md) |
| [`.github/workflows/`](.github/workflows/) | CI, deploy e ciclo de vida do banco | [CI/CD](#cicd-e-infraestrutura) |

## Funcionalidades

### Núcleo (MVP — Marcos 1 a 6)

| Módulo | Funcionalidades |
|---|---|
| Autenticação | Cadastro, login, access token JWT e renovação de sessão por cookie seguro |
| Contas | Organização de contas financeiras, arquivamento e preservação do histórico |
| Categorias | Classificação de receitas e despesas, com proteção de categorias associadas a lançamentos |
| Lançamentos | Registro de movimentações vinculadas às contas e categorias do usuário |
| Dashboard | Resumo financeiro, despesas por categoria e evolução do saldo |
| Orçamentos | Limites mensais por categoria e alertas quando ultrapassados |
| Metas de economia | Acompanhamento do progresso a partir dos lançamentos vinculados |
| Recorrências | Geração agendada de lançamentos recorrentes |

### Expansão (Marcos 7 a 15)

| Área | Funcionalidades |
|---|---|
| Acesso | Recuperação de senha por e-mail com token de uso único |
| Importação de dados | Extratos CSV com pré-visualização e identificação de possíveis duplicatas, que nunca são descartadas em silêncio |
| Planejamento financeiro | Contas a pagar e receber, parcelamentos, transferências entre contas e fluxo de caixa previsto × realizado |
| Cartões e dívidas | Cartões de crédito, faturas por ciclo de fechamento, empréstimos e financiamentos (Price, SAC) com amortização |
| Relatórios | DRE pessoal por competência, comparativo de períodos e exportação CSV |
| Patrimônio | Bens com avaliações, balanço pessoal (ativos − passivos) e evolução patrimonial |
| Investimentos | Carteira de ativos, custo médio, rentabilidade, proventos, comparativo com o CDI e cotações automáticas |
| Tributação | Apoio à declaração do IRPF, com estimativa completa × simplificada e apuração de renda variável — cada valor indica sua fonte e não substitui o programa da Receita |
| Proteção e longo prazo | Seguros com alerta de renovação e simulador de independência financeira |

Uma regra atravessa todas as áreas: **cada movimentação conta uma única vez**. Transferências, pagamento de fatura, compra de investimento e amortização de principal não são receita nem despesa; só o fato econômico (a compra no cartão, os juros, o provento) entra nos relatórios.

A importação de extratos cobre CSV; OFX está fora do escopo da primeira versão. O que vem a seguir está no [roadmap](docs/roadmap.md), e o que mudou em cada marco, no [CHANGELOG](CHANGELOG.md).

## Arquitetura

### Vertical slices

O backend é organizado por funcionalidades de negócio, em vez de concentrar a aplicação em camadas técnicas compartilhadas. Cada módulo reúne schema, regras de negócio, persistência, rotas e testes em `backend/src/features/<nome>/`.

O módulo `transactions` funciona como núcleo do domínio financeiro. Os demais módulos dependem dele (nunca o contrário) e acessam suas operações apenas pela camada pública de serviços, nunca consultando diretamente o repositório de outra funcionalidade. Essa organização reduz o acoplamento e permite evoluir e testar cada funcionalidade isoladamente.

O frontend espelha a mesma divisão em `frontend/src/features/<nome>/`.

**Detalhes:** [anatomia de uma slice](backend/README.md#anatomia-de-uma-slice) · [arquitetura por vertical slices](docs/arquitetura/visao-geral.md#vertical-slices)

### Decisões arquiteturais

As decisões de maior impacto foram registradas em ADRs, com justificativas e alternativas consideradas.

| ADR | Decisão |
|---|---|
| [001](docs/decisoes/ADR-001-cloud-provider-azure.md) | Azure como provedor de nuvem |
| [002](docs/decisoes/ADR-002-multi-user-from-start.md) | Aplicação multiusuário desde o início, mesmo sendo de uso pessoal |
| [003](docs/decisoes/ADR-003-sqlalchemy-over-sqlmodel.md) | SQLAlchemy 2.0 em vez de SQLModel |
| [004](docs/decisoes/ADR-004-custom-auth-implementation.md) | Autenticação implementada no projeto em vez de biblioteca pronta |
| [005](docs/decisoes/ADR-005-apscheduler-over-celery.md) | APScheduler em vez de Celery + Redis para os jobs agendados |
| [006](docs/decisoes/ADR-006-jwt-httponly-cookie.md) | Access token só em memória e refresh token em cookie `httpOnly`, nunca em `localStorage` |
| [007](docs/decisoes/ADR-007-vertical-slices-transactions-kernel.md) | Vertical slices com `transactions` como núcleo desacoplado |
| [010](docs/decisoes/ADR-010-transferencia-como-conceito-proprio.md) | Transferência como conceito próprio, neutra no resultado |
| [013](docs/decisoes/ADR-013-dre-competencia-fluxo-caixa.md) | DRE por competência e fluxo por caixa |

A lista completa, com 21 decisões, está em [docs/decisoes](docs/decisoes/README.md).

## Segurança e integridade dos dados

Segurança e consistência financeira são requisitos de arquitetura, não funcionalidades opcionais.

- **Isolamento entre usuários:** toda consulta filtra pelo `user_id` do token autenticado, e cada slice tem testes que provam que um usuário não acessa os dados de outro.
- **Proteção contra abuso:** rate limiting no login e na recuperação de senha.
- **Sessões:** cookie de refresh `httpOnly` com `SameSite=Strict` e header obrigatório nas rotas que dependem só do cookie.
- **Recuperação de senha:** apenas o hash do token é armazenado, e a resposta não revela se uma conta existe.
- **Importação de arquivos:** só CSV, até 2 MB e 5.000 linhas; erros de parsing viram mensagens por linha.
- **Acesso ao banco:** SQLAlchemy ORM exclusivamente, sem SQL montado por concatenação.
- **Gestão de segredos:** *secrets* do Container App e do GitHub, login no Azure por OIDC, sem credenciais no código-fonte.

**Detalhes:** [threat model e controles](docs/arquitetura/seguranca.md). Para relatar uma vulnerabilidade, veja a [política de segurança](SECURITY.md).

## Stack tecnológica

| Camada | Tecnologias |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, APScheduler |
| Banco de dados | PostgreSQL 16 (Azure Database for PostgreSQL Flexible Server) |
| Frontend | Next.js (App Router, static export), React, shadcn/ui, Tailwind CSS, Recharts |
| Testes | pytest e Testcontainers no backend; roteiros Playwright para as telas |
| Containers e nuvem | Docker, Azure Container Apps e Azure Container Registry |
| CI/CD | GitHub Actions com login no Azure via OIDC |

## Início rápido

Pré-requisitos: Docker, Node.js 22 e, para os testes, Python 3.12.

```bash
docker compose up -d          # PostgreSQL (localhost:5544) e API (localhost:8001)

cd frontend
cp .env.local.example .env.local
npm install
npm run dev                   # http://localhost:3000
```

As migrações rodam automaticamente na subida da API. Configuração, testes e execução fora do Docker estão nos guias do [backend](backend/README.md) e do [frontend](frontend/README.md).

## CI/CD e infraestrutura

Backend e frontend rodam em Azure Container Apps, com imagens no Azure Container Registry e banco em PostgreSQL Flexible Server. O frontend é um site estático servido por nginx no mesmo tipo de recurso que a API.

| Workflow | Responsabilidade |
|---|---|
| [`ci.yml`](.github/workflows/ci.yml) | Testes do backend e lint/build do frontend a cada push ou pull request |
| [`deploy.yml`](.github/workflows/deploy.yml) | Disparo manual: roda o CI, liga o banco, publica as imagens (tag = SHA do commit), atualiza os Container Apps e aguarda a nova revisão do backend responder no `/health` |
| [`db-lifecycle.yml`](.github/workflows/db-lifecycle.yml) | Liga o banco às 06h e desliga às 23h (horário de Brasília), todos os dias; também aceita acionamento manual |

O login no Azure usa OIDC com credenciais federadas, sem segredo de longa duração no GitHub. Os secrets do repositório são:

| Secret | Uso |
|---|---|
| `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` | Login no Azure (obrigatórios) |
| `ACS_CONNECTION_STRING`, `EMAIL_SENDER_ADDRESS` | E-mail real de recuperação de senha via Azure Communication Services (opcionais; sem eles o link só aparece no log) |
| `BRAPI_TOKEN` | Cotações automáticas de ações, FIIs e ETFs (opcional; sem ele a brapi atende só ativos de teste) |

Passo a passo de publicação, roteiro de fumaça e reversão: [Deploy e operação](docs/guias/deploy-e-operacao.md).

## Documentação

A documentação é versionada junto ao código, em [`docs/`](docs/README.md), organizada por tipo de leitura:

| Quero... | Leia |
|---|---|
| Entender o produto e suas regras de dinheiro | [Visão do produto](docs/produto/visao-geral.md) · [Regras de negócio](docs/produto/regras-de-negocio.md) |
| Entender a arquitetura | [Arquitetura](docs/arquitetura/visao-geral.md) · [Modelo de dados](docs/arquitetura/modelo-de-dados.md) · [Segurança](docs/arquitetura/seguranca.md) |
| Saber por que algo foi decidido | [Decisões (ADRs)](docs/decisoes/README.md) |
| Rodar, testar e publicar | [Ambiente local](docs/guias/ambiente-local.md) · [Deploy e operação](docs/guias/deploy-e-operacao.md) |
| Acompanhar a evolução | [Roadmap](docs/roadmap.md) · [CHANGELOG](CHANGELOG.md) · [Documentos de marco](docs/marcos/README.md) |
| Ver como o projeto foi pensado | [Discovery original](docs/historico/README.md) |

## Contribuindo

Relatos de bug, sugestões e pull requests são bem-vindos. O fluxo, os padrões de código, os testes exigidos e os termos das contribuições estão no [guia de contribuição](CONTRIBUTING.md).

## Licença

Copyright (c) 2026 Julia Cancio. **Todos os direitos reservados.** O código está público para consulta e avaliação; o uso, a cópia ou a redistribuição exigem autorização prévia. Veja o arquivo [LICENSE](LICENSE).

---

**CashTrail** — um projeto de engenharia de software orientado a domínio, segurança, consistência financeira e evolução incremental.
