# CashTrail — Definição da Stack (FASE 7)

## Backend: Python + FastAPI

- **Por que atende**: Python é a stack que você usa profissionalmente hoje (FATO, ver `01-discovery.md`) — mais honesto e mais forte numa entrevista do que aprender uma stack nova só pro portfólio. FastAPI gera OpenAPI/Swagger automático, tem validação nativa via Pydantic e é o framework Python mais adotado para APIs modernas.
- **Alternativas consideradas**: Java/Spring Boot (já dominado por você via TCC, mas não é prática atual — ver decisão original em `00-project-brief.md`); Django REST Framework (mais "baterias inclusas", porém mais pesado e opinativo do que o projeto precisa).
- **Trade-offs**: FastAPI tem ecossistema um pouco menos maduro que Django em algumas áreas (admin pronto, auth pronta), mas isso é aceitável — o objetivo é demonstrar como *você* implementa essas peças, não usar tudo pronto.
- **Confiança**: Alta.

### ORM e migrations

**DECISÃO:** SQLAlchemy 2.0 ou SQLModel?

**ALTERNATIVAS:**
1. **SQLAlchemy 2.0** — ORM mais maduro e adotado do ecossistema Python, usado por praticamente qualquer empresa que roda Python em produção.
2. **SQLModel** — criado pelo mesmo autor do FastAPI, une modelo ORM e schema Pydantic na mesma classe, reduz duplicação de código.

**EVIDÊNCIAS**: SQLModel é mais recente, tem comunidade e maturidade menores; unir ORM e schema Pydantic na mesma classe facilita no começo mas tende a vazar detalhes de banco pra API conforme o projeto cresce — o próprio plano original já registrava a intenção de "schemas Pydantic próprios, sem vazar modelos ORM na API", o que é mais natural com SQLAlchemy puro + Pydantic separado.

**TRADE-OFFS**: SQLAlchemy exige escrever schema Pydantic e modelo ORM separadamente (mais código), mas isso é exatamente a separação de responsabilidades que qualquer entrevistador técnico espera ver. SQLModel economiza digitação mas é uma habilidade de mercado menos reconhecida/menos exigida em vagas do que SQLAlchemy.

**RECOMENDAÇÃO**: SQLAlchemy 2.0 (com `Mapped`/`mapped_column`, estilo moderno) + Alembic para migrations + Pydantic schemas próprios por camada.

**POR QUÊ**: é a habilidade mais transferível/reconhecida no mercado, e reforça a separação de camadas que já era um objetivo explícito do projeto.

**CONFIANÇA**: Alta.

### Autenticação

**DECISÃO:** implementar JWT manualmente (bibliotecas de baixo nível) ou usar uma lib "baterias inclusas" (ex: `fastapi-users`)?

**ALTERNATIVAS:**
1. **Implementação própria** com `passlib`/`argon2-cffi` (hash de senha) + `python-jose` ou `PyJWT` (tokens) + rotas de auth escritas por você.
2. **`fastapi-users`**: resolve registro, login, verificação de e-mail, JWT, refresh token e até login social prontos.

**EVIDÊNCIAS**: `fastapi-users` reduz risco de erro de segurança (é testada e mantida), mas é uma "caixa preta" do ponto de vista de portfólio — um recrutador pode perguntar "como você implementou JWT" e a resposta "usei uma lib pronta" demonstra menos profundidade do que implementar você mesma com os primitivos corretos.

**TRADE-OFFS**: implementação própria exige mais cuidado (é fácil errar expiração de token, invalidação de refresh token, hashing) — os requisitos SEC-001/002/006 (`03-requirements.md`) já cobrem os pontos que precisam de atenção redobrada nos testes.

**RECOMENDAÇÃO**: implementação própria, com `argon2-cffi` (hash) + `PyJWT` (tokens), seguindo os requisitos SEC já levantados e cobertura de teste dedicada pra RNF-001 (isolamento por usuário).

**POR QUÊ**: o próprio propósito do projeto é provar competência, e autenticação é um dos tópicos mais cobrados em entrevista backend júnior/pleno.

**CONFIANÇA**: Média — exige disciplina de teste e revisão de segurança (FASE 11) pra não introduzir vulnerabilidade; risco mitigável, não motivo pra trocar de abordagem.

### Testes

- **Pytest** + `httpx`/`TestClient` (testes de API) + **Testcontainers-Python** (sobe um Postgres real em container pra testes de integração, evitando "funciona no SQLite mas quebra no Postgres real").
- **Por que**: já era a escolha original, validada — Testcontainers é o padrão de mercado pra evitar mocks que escondem bugs de integração real (relevante, já que isso não é o mesmo risco do "banco mockado" mas seria o equivalente ORM: testar contra o banco real de verdade).
- **Confiança**: Alta.

### Job agendado (lançamentos recorrentes)

**Decisão tomada com você**: **APScheduler**, rodando dentro do próprio processo da API — sem Celery, sem Redis, sem broker adicional.
- **Por quê**: o projeto tem exatamente um job periódico (gerar lançamentos recorrentes). Celery+Redis adicionaria um serviço a mais pra manter, testar e pagar na Azure, sem necessidade concreta proporcional ao problema (regra geral da FASE 7: evitar filas/infra extra sem necessidade real).
- Se no futuro o projeto crescer para múltiplos jobs assíncronos pesados (ex: processamento de importação de extratos muito grandes em background), Celery volta a ser uma opção válida — não fechamos essa porta, só não a abrimos agora sem necessidade.

## Frontend: Next.js (App Router) + shadcn/ui + Tailwind CSS

- **Por que atende**: desacoplado do backend via REST/JWT, então não há necessidade técnica de "combinar" com a stack do backend (decisão original já validada). shadcn/ui + Tailwind entregam visual polido rápido — importante pra impressão imediata de quem abre o link de demo.
- **Alternativas consideradas**: Angular (mais comum em shops corporativos Java, mas não há motivo técnico pra isso aqui já que backend é Python); React puro sem Next (perderia SSR/roteamento pronto).
- **Bibliotecas complementares**: Recharts (gráficos — dashboard, evolução de saldo), React Hook Form + Zod (formulários e validação, com schema compartilhável de intenção com o Pydantic do backend, mesmo que não literalmente compartilhado).
- **Confiança**: Alta.

## Banco de dados: PostgreSQL (Azure Database for PostgreSQL Flexible Server)

- Já decidido e custeado na FASE 5/6. Justificativa: relacional é adequado ao domínio (contas, categorias, lançamentos, orçamentos, metas têm relações claras e integridade referencial importa); PostgreSQL é o banco relacional mais usado no mercado Python/FastAPI.
- **Confiança**: Alta.

## Cloud: Azure

- **Container Apps** (backend), **Static Web Apps** com SPIKE pendente / **Vercel** como fallback (frontend), **Blob Storage** (arquivos de extrato), **Key Vault** (segredos — introduzido aqui como decorrência do SEC-005 de `03-requirements.md`, ainda não havia sido nomeado o serviço exato).
- Decisão de nuvem (Azure vs AWS) já resolvida na FASE 0.
- **Sem Kubernetes/AKS**: não há necessidade concreta de orquestração de containers pra uma única API + um frontend estático — Container Apps já resolve o caso de uso sem a complexidade operacional do AKS.

## Versionamento: Git + GitHub

- Monorepo único (`/backend`, `/frontend`, `/docs`), conforme decisão original. Repositório público (decisão implícita, já que é peça de portfólio) — o que também é o que torna o CI gratuito e ilimitado (FASE 5).

---

## Resumo da stack final

| Camada | Escolha | Alternativa descartada | Motivo principal |
|---|---|---|---|
| Backend | Python + FastAPI | Java/Spring Boot | Reflete stack profissional real atual |
| ORM | SQLAlchemy 2.0 + Alembic | SQLModel | Habilidade mais transferível, separação de camadas mais limpa |
| Auth | Implementação própria (argon2 + JWT) | fastapi-users | Demonstra profundidade técnica, tema cobrado em entrevista |
| Testes | Pytest + Testcontainers | Mocks de banco | Evita falso positivo de teste (bug só aparece no banco real) |
| Job agendado | APScheduler | Celery + Redis | Proporcional a um único job periódico, sem infra extra |
| Frontend | Next.js + shadcn/ui + Tailwind | Angular | Sem necessidade técnica de acoplar com stack do backend; visual pronto |
| Banco | PostgreSQL (Azure Flexible Server) | — | Relacional adequado ao domínio |
| Cloud | Azure (Container Apps, Static Web Apps/Vercel, Blob Storage, Key Vault) | AWS | Decisão já tomada na FASE 0 |
| CI/CD | GitHub Actions | — | Gratuito e ilimitado em repositório público |

---

**STATUS**: Pronto para avançar.

**PENDÊNCIA carregada (não bloqueante)**: SPIKE do Next.js híbrido no Azure Static Web Apps (`05-integrations.md`) ainda não executado — não impede desenhar a arquitetura, só precisa ser resolvido antes do deploy real do frontend.

Seguimos para a **FASE 8 — Desenho da Arquitetura**?
