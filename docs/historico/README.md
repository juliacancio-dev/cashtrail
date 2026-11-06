# Histórico: discovery original

Registro do discovery feito antes da primeira linha de código (setembro de 2026), em fases e com cinco *gates* de aprovação (problema, solução, viabilidade, arquitetura e execução). Ele mostra **como** o projeto foi pensado; não descreve o sistema de hoje.

**Não é atualizado.** Vários pontos foram superados depois: OFX e Blob Storage saíram do escopo, o frontend foi para Container Apps em vez de Static Web Apps, o roadmap original de 8 marcos virou 17. O que continua valendo está na documentação viva:

| Para saber... | Leia hoje | Origem aqui |
|---|---|---|
| O que é o produto | [produto/visao-geral.md](../produto/visao-geral.md) | 00, 01, 12 |
| Regras e requisitos | [regras de negócio](../produto/regras-de-negocio.md), [catálogo](../referencia/requisitos.md) | 03, 04 |
| Arquitetura e dados | [arquitetura](../arquitetura/visao-geral.md), [modelo de dados](../arquitetura/modelo-de-dados.md) | 07, 08, 09, 10 |
| Segurança | [segurança](../arquitetura/seguranca.md) | 11 |
| Decisões | [ADRs](../decisoes/README.md) | 07, 11 |
| Processo, DoR e DoD | [como trabalhamos](../processo/como-trabalhamos.md) | 19, 20 |
| Próximos passos | [roadmap](../roadmap.md) | 13, 14, 18 |

Os arquivos mantêm os nomes originais porque o código cita vários deles em comentários (por exemplo, `09-vertical-slices.md` e `10-data-model.md`). **Não renomeie.**

## Documentos

| Doc | Fase | Conteúdo |
|---|---|---|
| [00](discovery/00-project-brief.md) | — | Resumo executivo e decisões fundamentais |
| [01](discovery/01-discovery.md) | 0–1 | Mapa do problema, dores, personas, jornadas |
| [02](discovery/02-market-research.md) | 2 | Firefly III, Actual Budget, Mobills, Organizze; custo do Open Finance |
| [03](discovery/03-requirements.md) | 3 | RF, RNF, RB, SEC, INT, OPS originais |
| [04](discovery/04-usecases.md) | 4 | Fluxos e o critério de duplicata da importação (RB-006) |
| [05](discovery/05-integrations.md) | 5 | Serviços Azure pesquisados |
| [06](discovery/06-costs.md) | 6 | Custos e o achado sobre o crédito de estudante |
| [07](discovery/07-stack.md) | 7 | Stack e alternativas |
| [08](discovery/08-architecture.md) | 8 | Diagramas C4 originais |
| [09](discovery/09-vertical-slices.md) | 9 | Slices e dependências originais |
| [10](discovery/10-data-model.md) | 10 | Modelo de dados do MVP |
| [11](discovery/11-security.md) | 11 | Threat model original |
| [12](discovery/12-mvp.md) | 12 | Definição do MVP |
| [13](discovery/13-roadmap.md) | 13 | Roadmap original (Marcos 1 a 8) |
| [14](discovery/14-estimates.md) | 14 | Estimativas de esforço |
| [15](discovery/15-risks.md) | 15 | Registro de riscos |
| [17](discovery/17-traceability.md) | 17 | Rastreabilidade dor → requisito |
| [18](discovery/18-backlog.md) | 18 | Backlog inicial por épico |
| [19](discovery/19-definition-ready-done.md) | 22–23 | Definition of Ready e of Done |
| [20](discovery/20-gates-checkpoint.md) | 24 | Aprovação dos cinco gates |

Não há documento 16 (a fase foi incorporada a outras).
