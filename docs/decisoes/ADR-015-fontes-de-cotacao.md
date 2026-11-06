# ADR-015 — Cotações pela brapi e índices pelo Banco Central, atrás de uma interface

- **Status:** Aceita
- **Data:** 2026-10-15

## Contexto e problema

A carteira de investimentos precisa de cotações de renda variável e do CDI para comparar rentabilidade. O plano grátis da brapi permite 15.000 requisições por mês; o Banco Central (SGS) é oficial e aberto.

## Opções consideradas

1. **brapi** para renda variável + **valor manual** para o resto + **Banco Central** para índices, com cache e atualização controlada.
2. **Tudo manual.**
3. **Fonte não oficial** (scraping), sem contrato.

E, para a frequência: botão + job diário; a cada abertura de tela; ou só manual.

## Decisão

Escolhida: **opção 1**, atrás de uma interface `QuoteProvider` que permite trocar de fonte, com **botão "Atualizar cotações" + job diário** e um teto mensal configurável (`QUOTES_MONTHLY_CAP`, padrão 10.000).

## Consequências

- **Positivas:** renda variável atualizada sem esforço; falha da fonte não apaga nem bloqueia (vale a última cotação).
- **Negativas:** dependência externa e um token (`BRAPI_TOKEN`) que só pode existir no backend. Sem token, a brapi atende só ativos de teste (PETR4, VALE3, MGLU3, ITUB4).
- **Restrição dos termos de uso (lidos em 2026-10-22):** proibido redistribuir os dados a terceiros. Uso pessoal é compatível; se outras pessoas usarem a demonstração pública e virem cotações, isso pode ser lido como redistribuição.

## Mais informações

- [Integrações externas](../referencia/integracoes-externas.md).
