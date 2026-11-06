# ADR-004 — Autenticação própria em vez de `fastapi-users`

- **Status:** Aceita
- **Data:** 2026-09-16
- **Contexto de origem:** discovery, FASE 7 ([07-stack](../historico/discovery/07-stack.md))

## Contexto e problema

Cadastro, login e emissão de JWT podiam ser implementados no projeto ou vir prontos de uma biblioteca.

## Opções consideradas

1. **Implementação própria** com Argon2 (`argon2-cffi`) e PyJWT.
2. **`fastapi-users`**, biblioteca "baterias inclusas".

## Decisão

Escolhida: **implementação própria**, porque um dos objetivos do projeto é demonstrar profundidade técnica, e autenticação é um dos temas mais cobrados em entrevistas de backend. Uma biblioteca pronta reduziria o risco de bug, mas também a demonstração.

## Consequências

- **Positivas:** o fluxo inteiro (hash, tokens, refresh, troca de senha) é conhecido e testado no projeto.
- **Negativas:** exige disciplina de segurança; um erro aqui é do projeto, não de terceiros.
- **Mitigação:** testes de isolamento por usuário, rate limiting no login (SEC-006), revisão de segurança no Marco 6 e tokens invalidados após troca de senha.

## Mais informações

- [Segurança](../arquitetura/seguranca.md) e [ADR-006](ADR-006-jwt-httponly-cookie.md).
