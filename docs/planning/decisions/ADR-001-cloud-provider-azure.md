# ADR-001 — Provedor de nuvem: Azure (não AWS)

**Status**: Aceito

**Contexto**: Planejamento anterior do projeto (antes deste discovery formal) havia registrado AWS como nuvem escolhida. O prompt padrão de trabalho definido pela autora, porém, especifica Azure como padrão da stack.

**Alternativas**: AWS (decisão anterior) vs. Azure (padrão atual).

**Decisão**: Azure.

**Justificativa**: a autora possui Azure for Students (US$100 de crédito/12 meses), o que reduz a barreira de custo real; e é o padrão que ela definiu explicitamente para trabalhar daqui em diante.

**Consequências**: toda a pesquisa de serviços de nuvem (`05-integrations.md`), custos (`06-costs.md`) e arquitetura (`08-architecture.md`) foi feita em cima de serviços Azure (Container Apps, Static Web Apps, Blob Storage, Key Vault, PostgreSQL Flexible Server), não AWS.
