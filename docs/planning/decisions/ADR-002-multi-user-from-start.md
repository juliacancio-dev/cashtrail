# ADR-002 — Arquitetura multi-user desde o início

**Status**: Aceito

**Contexto**: há apenas uma usuária real confirmada (a própria autora) no momento do discovery.

**Alternativas**: (1) single-user, sem autenticação real; (2) multi-user completo (registro/login/JWT, `user_id` isolando dados em toda tabela).

**Decisão**: multi-user desde o início.

**Justificativa**: o custo de implementar agora é baixo; retrofitar isolamento por usuário depois seria caro e arriscado; autenticação/autorização correta é uma das provas técnicas mais visíveis num projeto de portfólio.

**Consequências**: todo o modelo de dados (`10-data-model.md`) tem `user_id` em toda tabela de domínio; todo requisito de segurança (RNF-001, SEC-002) exige teste dedicado de isolamento entre usuários.
