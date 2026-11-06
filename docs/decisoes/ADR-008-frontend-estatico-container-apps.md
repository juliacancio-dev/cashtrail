# ADR-008 — Frontend como site estático servido por nginx em Container Apps

- **Status:** Aceita
- **Data:** 2026-09-18

## Contexto e problema

O discovery previa hospedar o Next.js no Azure Static Web Apps. Na hora do deploy, a criação do recurso falhou com `RequestDisallowedByAzure`: a política da assinatura Azure for Students bloqueia esse tipo de recurso na região.

## Opções consideradas

1. **Vercel** — fora da Azure, com servidor Node gerenciado.
2. **Next.js com servidor Node** num Container App.
3. **Export estático** (`output: "export"`) servido por nginx num Container App, o mesmo tipo de recurso do backend.

## Decisão

Escolhida: **export estático com nginx em Container Apps**, porque mantém tudo numa nuvem e num tipo de recurso, não precisa de servidor Node em produção e o app já era todo de cliente (fala com a API pelo `api-client`).

## Consequências

- **Positivas:** imagem pequena (`nginx:alpine`), deploy igual ao do backend, nenhuma superfície de servidor no frontend.
- **Negativas:** sem recursos de servidor do Next.js (Server Actions, rotas de API, middleware, rotas dinâmicas sem `generateStaticParams`). `NEXT_PUBLIC_API_URL` é embutida no build: mudar a URL da API exige nova imagem.
- **Revisar se:** o app precisar de renderização no servidor ou se a política da assinatura mudar.

## Mais informações

- [Por que static export](../../frontend/README.md#por-que-static-export) e [Build e Docker](../../frontend/README.md#build-e-docker).
