# CashTrail — Definition of Ready / Definition of Done (FASE 22-23 da metodologia)

## Definition of Ready (antes de uma Vertical Slice entrar em desenvolvimento)

Uma slice só começa a ser implementada quando tiver:
- [ ] Objetivo claro (qual dor/RF ela resolve — ver `17-traceability.md`)
- [ ] Comportamento definido (fluxo em `04-usecases.md`, se aplicável)
- [ ] Requisitos conhecidos (RF/RNF/RB/SEC relacionados em `03-requirements.md`)
- [ ] Critérios de aceitação (ver `18-backlog.md`)
- [ ] Dependências identificadas (outras slices/marcos, ver `13-roadmap.md`)
- [ ] Arquitetura compatível (segue o padrão de `09-vertical-slices.md`)
- [ ] Dados necessários definidos (`10-data-model.md`)
- [ ] Integrações conhecidas (`05-integrations.md`, se aplicável)
- [ ] Riscos relevantes identificados (`15-risks.md`)
- [ ] Estratégia de teste definida (unitário + integração com Testcontainers, conforme `07-stack.md`)

Todas as slices do MVP (Epics 2-6 do backlog) já atendem a esse checklist com base nos documentos produzidos neste discovery — nenhuma está bloqueada por falta de definição.

## Definition of Done (por Vertical Slice)

Uma slice só é considerada concluída quando:
- [ ] Comportamento implementado conforme o fluxo definido
- [ ] Validações implementadas (Pydantic)
- [ ] Regras de negócio implementadas (RB relacionadas)
- [ ] Persistência funcionando (migration Alembic aplicada)
- [ ] Integrações funcionando, quando aplicável
- [ ] Tratamento de erros implementado
- [ ] Testes adequados (unitário + integração real via Testcontainers)
- [ ] Segurança considerada (isolamento por `user_id`, validação de entrada)
- [ ] Logs mínimos necessários (OPS-004)
- [ ] Documentação atualizada (README da slice/da API, se necessário)
- [ ] Critérios de aceitação da `17-traceability.md`/`18-backlog.md` atendidos

"Código escrito" não é "feature pronta" — uma slice sem teste de integração real ou sem checagem de isolamento por usuário não está concluída, mesmo que funcione manualmente uma vez.
