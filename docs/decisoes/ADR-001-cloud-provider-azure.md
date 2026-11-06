# ADR-001 — Azure como provedor de nuvem

- **Status:** Aceita
- **Data:** 2026-09-16
- **Contexto de origem:** discovery, FASE 0 ([brief](../historico/discovery/00-project-brief.md))

## Contexto e problema

Um planejamento informal anterior ao discovery apontava a AWS. O padrão de stack definido pela autora para os projetos seguintes, porém, é a Azure, e ela tem a assinatura **Azure for Students** (US$ 100 de crédito por 12 meses). Era preciso escolher uma nuvem antes de pesquisar serviços, custos e arquitetura.

## Opções consideradas

1. **AWS** — a escolha do planejamento informal.
2. **Azure** — o padrão de stack da autora, com crédito de estudante disponível.

## Decisão

Escolhida: **Azure**, porque reduz o custo real a quase zero no primeiro ano e é a nuvem que a autora definiu como padrão de trabalho.

## Consequências

- **Positivas:** custo coberto pelo crédito; uma única nuvem para estudar e documentar.
- **Negativas:** a assinatura de estudante tem políticas que bloqueiam alguns recursos (Static Web Apps, por exemplo; ver [ADR-008](ADR-008-frontend-estatico-container-apps.md)); o crédito anual limita quanto tempo o banco pode ficar ligado.
- **Revisar se:** o crédito acabar e o custo mensal passar do que faz sentido para um projeto pessoal.

## Mais informações

- Pesquisa de serviços e custos: [05-integrations](../historico/discovery/05-integrations.md), [06-costs](../historico/discovery/06-costs.md).
- Infraestrutura atual: [Deploy e operação](../guias/deploy-e-operacao.md).

> **Nota (2026-11-04):** o texto original listava Static Web Apps e Blob Storage entre os serviços previstos. Nenhum dos dois é usado: o frontend roda em Container Apps ([ADR-008](ADR-008-frontend-estatico-container-apps.md)) e os extratos importados não são guardados (só o resultado da importação vai para o banco).
