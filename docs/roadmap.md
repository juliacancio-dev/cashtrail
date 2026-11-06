# Roadmap

Estado dos marcos, o que vem a seguir e o que está guardado para depois. O histórico detalhado de cada entrega está no [CHANGELOG](../CHANGELOG.md); o desenho de cada marco, em [marcos/](marcos/README.md).

*Atualizado em 2026-11-04.*

## Estado

| Marco | Entrega | Situação |
|---|---|---|
| 1 | Discovery e documentação | concluído |
| 2 | Autenticação, contas e primeiro deploy | em produção |
| 3–6 | MVP: categorias, lançamentos, dashboard, orçamentos, metas, recorrências, hardening | em produção |
| 7 | Recuperação de senha e importação de extrato CSV | em produção |
| 8–10 | Contas a pagar e a receber, transferências, cartões, DRE e fluxo de caixa | em produção |
| 11–12 | Dívidas, bens e patrimônio | em produção |
| 13–15 | Investimentos, IRPF, seguros e independência financeira | em produção |
| 16 | Redesign: calendário do dinheiro, tema claro e escuro | concluído, **não publicado** |
| 17 | Acabamento: navegação e telas densas no estilo calmo | **em andamento** |

A produção roda o código até a correção do DRE de 2026-10-22. Os Marcos 16 e 17 sobem juntos no próximo deploy em lote.

## Em andamento: Marco 17

[Documento do marco](marcos/33-marco-17-acabamento.md)

| Etapa | O que | Situação |
|---|---|---|
| 1 | Defeitos: datas no fuso local, datas formatadas, título do Resumo | feita |
| 2 | Navegação em cápsula com gaveta no logo | feita |
| 3 | Resumo do mês: um número, uma frase, avisos numa lista | feita |
| 4 | Lançamentos: um mês por vez, agrupados por dia | a fazer |
| 5 | Compromissos: uma frase de totais, filtros recolhidos, ação principal na linha | a fazer |
| 6 | Cartões: só a fatura atual aberta | a fazer |

## Próximos

| Marco | Ideia | Estado |
|---|---|---|
| 18 | **Colchão**: mínimo em caixa por usuário e alerta "a previsão fura o colchão no dia X" | ideia; precisa de documento de desenho |
| — | Deploy em lote dos Marcos 16 e 17 | quando a mantenedora decidir |

## Backlog

Sem ordem de prioridade. Cada item vira marco ou etapa só com documento de desenho.

**Produto**

- Previsão com a média dos gastos variáveis (hoje a previsão só conhece o que está agendado).
- As outras 16 telas no estilo calmo.
- Alertas por e-mail: renovação de seguro, DARF do mês.
- Investimentos: cotação automática do Tesouro Direto, rentabilidade ponderada pelo tempo (TWR/XIRR), desdobramentos automáticos.
- IRPF: day trade, ETF, BDR, cripto e fundos.
- Importação OFX.

**Técnico**

- Trocar o e-mail do ACS por SMTP **antes de 2028-09-30** ([ADR-017](decisoes/ADR-017-email-azure-communication-services.md)).
- "Hoje" no fuso `America/Sao_Paulo` no backend (exige `tzdata` na imagem).
- Pré-carregamento do Next 16 gerando 404 no nginx ([doc 33](marcos/33-marco-17-acabamento.md)).
- Monitoramento e alertas de produção.
- Key Vault com referência viva no Container App.
- Dependabot para pip, npm e GitHub Actions.
- Renumerar os IDs duplicados RF-032–037 e RB-023–029 dos Marcos 11 e 12 ([catálogo](referencia/requisitos.md#colisões-de-numeração)).

**Recorrente**

- Todo ano: [atualização dos parâmetros do IRPF](guias/atualizacao-anual-irpf.md).

## Validações com dados reais pendentes

Coisas que só a mantenedora pode conferir e que testes sintéticos não substituem:

- importar um **extrato real** do banco (o parser só viu amostras sintéticas, como [`exemplos/extrato-exemplo.csv`](exemplos/extrato-exemplo.csv));
- conferir a regra de fatura com o **fechamento e o vencimento do cartão real**;
- comparar a estimativa do IRPF com o **programa da Receita**.
