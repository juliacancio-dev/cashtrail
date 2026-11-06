# ADR-016 — Parâmetros fiscais versionados por ano-calendário

- **Status:** Aceita
- **Data:** 2026-10-15

## Contexto e problema

O apoio ao IRPF usa tabela progressiva, limites de dedução, desconto simplificado e redutor, que mudam a cada ano (e mudaram no meio de 2026, com a Lei 15.270/2025). Não há API oficial verificada de tabelas.

## Opções consideradas

1. **Dados versionados por ano-calendário**, com fonte e data, carregados pela lógica.
2. **Constantes no código.**
3. **Buscar de uma fonte online** a cada uso.

## Decisão

Escolhida: **dados versionados por ano**, em `backend/src/features/tax/parameters/<ano>.json`, cada um com a fonte, a data da consulta e a lista do que não foi verificado. Ano sem arquivo é erro explícito (HTTP 422), nunca um valor presumido. O produto é **apoio à declaração**: não gera o arquivo da Receita nem transmite nada.

## Consequências

- **Positivas:** trocar de ano não mexe em regra; cada ano tem teste próprio; a tela mostra a fonte e as premissas não verificadas.
- **Negativas:** alguém precisa criar o arquivo do ano novo, com fonte oficial, todo ano. O passo a passo está em [Atualização anual do IRPF](../guias/atualizacao-anual-irpf.md).

## Mais informações

- [Imposto de renda](../produto/regras-de-negocio.md#9-imposto-de-renda-irpf).
