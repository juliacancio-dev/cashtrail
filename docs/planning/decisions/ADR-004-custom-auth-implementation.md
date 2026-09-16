# ADR-004 — Implementação própria de autenticação (não `fastapi-users`)

**Status**: Aceito

**Contexto**: escolha de como implementar registro/login/JWT no backend.

**Alternativas**: implementação própria (argon2 + PyJWT) vs. `fastapi-users` (biblioteca "baterias inclusas").

**Decisão**: implementação própria.

**Justificativa**: o objetivo central do projeto é demonstrar competência técnica; autenticação é um dos temas mais cobrados em entrevista backend; uma lib pronta reduziria a demonstração de profundidade, mesmo reduzindo risco de bug.

**Consequências**: exige disciplina extra de segurança e teste (ver `11-security.md`, threat model, e RNF-001). Risco aceito e mitigado com teste dedicado de isolamento por usuário e revisão de segurança no Marco 6 do roadmap.
