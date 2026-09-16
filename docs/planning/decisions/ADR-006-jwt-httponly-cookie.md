# ADR-006 — Refresh token em cookie `httpOnly` (não `localStorage`)

**Status**: Aceito

**Contexto**: onde armazenar o JWT no navegador.

**Alternativas**: ambos os tokens em `localStorage` vs. refresh token em cookie `httpOnly`+`Secure`+`SameSite=Strict` com access token só em memória.

**Decisão**: refresh token em cookie `httpOnly`; access token nunca persistido, só em memória (estado React).

**Justificativa**: `localStorage` é acessível por qualquer JavaScript rodando na página — uma vulnerabilidade de XSS (mesmo de uma dependência de terceiro) rouba o token trivialmente. Cookie `httpOnly` elimina essa classe de ataque.

**Consequências**: exige CORS com `credentials: include` configurado corretamente entre os domínios de frontend e backend na Azure — validado como parte do Marco 2 do roadmap (primeira Vertical Slice).
