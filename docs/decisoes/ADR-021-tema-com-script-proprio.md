# ADR-021 — Tema claro e escuro com script próprio, sem biblioteca

- **Status:** Aceita
- **Data:** 2026-10-26

## Contexto e problema

O app ganhou modo claro e escuro. Como é um site estático ([ADR-008](ADR-008-frontend-estatico-container-apps.md)), não há servidor para saber o tema antes de a página pintar, e o tema errado pode "piscar" ao abrir.

## Opções consideradas

1. **`next-themes`**, que resolve o piscar e a sincronia entre abas.
2. **Script próprio** de poucas linhas no `<head>`, que aplica a classe `dark` antes da primeira pintura, mais um botão que troca e salva.

## Decisão

Escolhida: **script próprio**. A primeira visita segue o tema do sistema; a escolha no botão fica salva no navegador e passa a valer. São poucas linhas, fáceis de explicar numa revisão, sem uma dependência para algo tão pequeno.

## Consequências

- **Positivas:** nenhuma dependência nova; comportamento coberto pelo roteiro `scripts/e2e/e2e-m16-tema.mjs`.
- **Negativas:** os cuidados ficam no projeto: rodar antes da pintura, `try/catch` no `localStorage`, `suppressHydrationWarning` no `<html>`.

## Mais informações

- Tokens de cor e contraste: [doc 32, decisão 6](../marcos/32-marco-16-redesign.md) e [doc 33, decisão 8](../marcos/33-marco-17-acabamento.md).
