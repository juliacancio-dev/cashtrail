# Registros de decisão (ADRs)

Cada arquivo registra **uma** decisão difícil de desfazer: o contexto, as opções consideradas, a escolha e as consequências. O formato segue o [MADR](https://adr.github.io/madr/) (*Markdown Architectural Decision Records*), em versão enxuta e em português.

## Índice

| ADR | Decisão | Status | Data |
|---|---|---|---|
| [001](ADR-001-cloud-provider-azure.md) | Azure como provedor de nuvem | Aceita | 2026-09-16 |
| [002](ADR-002-multi-user-from-start.md) | Multiusuário desde o início | Aceita | 2026-09-16 |
| [003](ADR-003-sqlalchemy-over-sqlmodel.md) | SQLAlchemy 2.0 em vez de SQLModel | Aceita | 2026-09-16 |
| [004](ADR-004-custom-auth-implementation.md) | Autenticação própria em vez de `fastapi-users` | Aceita | 2026-09-16 |
| [005](ADR-005-apscheduler-over-celery.md) | APScheduler em vez de Celery + Redis | Aceita | 2026-09-16 |
| [006](ADR-006-jwt-httponly-cookie.md) | Access token em memória e refresh token em cookie `httpOnly` | Aceita | 2026-09-16 |
| [007](ADR-007-vertical-slices-transactions-kernel.md) | Vertical slices com `transactions` como núcleo | Aceita | 2026-09-16 |
| [008](ADR-008-frontend-estatico-container-apps.md) | Frontend como site estático servido por nginx em Container Apps | Aceita | 2026-09-18 |
| [009](ADR-009-partida-simples.md) | Partida simples, sem partidas dobradas | Aceita | 2026-10-06 |
| [010](ADR-010-transferencia-como-conceito-proprio.md) | Transferência como conceito próprio, neutra no resultado | Aceita | 2026-10-09 |
| [011](ADR-011-fatura-calculada.md) | Fatura do cartão calculada a partir das compras | Aceita | 2026-10-09 |
| [012](ADR-012-contas-nao-caixa.md) | Cartão, dívida e investimento como tipos de conta | Aceita | 2026-10-09 |
| [013](ADR-013-dre-competencia-fluxo-caixa.md) | DRE por competência e fluxo por caixa, numa slice só de leitura | Aceita | 2026-10-09 |
| [014](ADR-014-patrimonio-calculado.md) | Patrimônio histórico calculado na hora, sem snapshots | Aceita | 2026-10-15 |
| [015](ADR-015-fontes-de-cotacao.md) | Cotações pela brapi e índices pelo Banco Central, atrás de uma interface | Aceita | 2026-10-15 |
| [016](ADR-016-parametros-fiscais-por-ano.md) | Parâmetros fiscais versionados por ano-calendário | Aceita | 2026-10-15 |
| [017](ADR-017-email-azure-communication-services.md) | E-mail transacional pelo Azure Communication Services | Aceita | 2026-10-08 |
| [018](ADR-018-migracoes-na-subida.md) | Migrações aplicadas na subida do container | Aceita | 2026-09-28 |
| [019](ADR-019-texto-com-check-em-vez-de-enum.md) | Texto com `CHECK` em vez de enum nativo para valores novos | Aceita | 2026-10-08 |
| [020](ADR-020-calendario-como-tela-inicial.md) | Calendário do dinheiro como tela inicial, calculado no backend | Aceita | 2026-10-26 |
| [021](ADR-021-tema-com-script-proprio.md) | Tema claro e escuro com script próprio, sem biblioteca | Aceita | 2026-10-26 |

As datas dos ADRs 008 a 021 são as da decisão original; eles foram escritos em 2026-11-04, a partir dos [documentos de marco](../marcos/README.md), quando a documentação foi reorganizada.

## Quando escrever um ADR

Escreva quando a decisão:

- é cara de desfazer (banco, nuvem, modelo de dados, forma de contar dinheiro);
- tinha alternativas reais, com trade-offs que alguém vai questionar numa revisão;
- muda uma regra que outras partes do código assumem.

Escolhas de estilo, nomes e detalhes de interface ficam no documento do marco, não aqui.

## Como escrever

1. Copie o [template](template.md) para `ADR-NNN-titulo-curto.md`, com o próximo número livre.
2. Preencha contexto, opções, decisão e consequências. Liste as opções descartadas e o motivo.
3. Abra o pull request com o status **Proposta**; ao aprovar, mude para **Aceita** e acrescente a linha no índice acima.

Um ADR aceito **não é reescrito**. Se a decisão mudar, crie um ADR novo, marque o antigo como **Substituída por ADR-NNN** e aponte de volta. Correções de link e notas de atualização curtas são permitidas.

O código cita ADRs pelo identificador (`ADR-006`) nos comentários que explicam o porquê de uma regra.
