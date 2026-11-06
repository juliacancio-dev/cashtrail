# ADR-006 — Access token em memória e refresh token em cookie `httpOnly`

- **Status:** Aceita
- **Data:** 2026-09-16
- **Contexto de origem:** discovery, FASE 11 ([11-security](../historico/discovery/11-security.md))

## Contexto e problema

O frontend é uma SPA que fala com uma API própria. Era preciso decidir onde guardar os tokens no navegador.

## Opções consideradas

1. **Os dois tokens em `localStorage`**, enviados no header `Authorization`.
2. **Refresh token em cookie `httpOnly` + `Secure` + `SameSite=Strict`**, e access token só em memória.

## Decisão

Escolhida: **opção 2**. Qualquer JavaScript da página lê o `localStorage`, então um XSS, mesmo vindo de uma dependência, roubaria os tokens. O cookie `httpOnly` elimina essa classe de ataque.

## Consequências

- **Positivas:** o refresh token nunca fica acessível a JavaScript; recarregar a página não perde a sessão (o refresh silencioso emite um novo access token).
- **Negativas:** exige CORS com `credentials: include` e defesa contra CSRF. As rotas que dependem só do cookie (`/auth/refresh`, `/auth/logout`) exigem o header `X-Requested-With`.
- **Restrição prática:** frontend e backend precisam ser o mesmo "site" para o `SameSite=Strict`. Em produção os dois ficam sob `azurecontainerapps.io`; localmente, use sempre `localhost`, nunca `127.0.0.1`.

## Mais informações

- [Autenticação no frontend](../../frontend/README.md#autenticação) e [no backend](../../backend/README.md#autenticação-nas-rotas).
