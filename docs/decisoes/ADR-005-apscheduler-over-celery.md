# ADR-005 — APScheduler em vez de Celery + Redis

- **Status:** Aceita
- **Data:** 2026-09-16

## Contexto e problema

A geração de lançamentos recorrentes exige um job periódico. Na época era o único job do sistema.

## Opções consideradas

1. **APScheduler** rodando dentro do processo da API.
2. **Celery + Redis**, com fila e worker dedicados.

## Decisão

Escolhida: **APScheduler**, porque Celery e Redis acrescentariam dois serviços para manter, testar e pagar na Azure sem necessidade proporcional ao problema.

## Consequências

- **Positivas:** operação mais simples e mais barata; um container a menos.
- **Negativas:** o agendador só existe enquanto o container está de pé. Com o Container App escalando a zero, os jobs passaram a rodar também **na subida** (recorrências e cotações), e o botão "Atualizar cotações" é o caminho confiável.
- **Revisar se:** surgirem vários jobs pesados ou que precisem de garantia de execução mesmo sem tráfego.

## Mais informações

- [Jobs agendados](../../backend/README.md#jobs-agendados). Hoje são dois: recorrências e cotações ([ADR-015](ADR-015-fontes-de-cotacao.md)).
