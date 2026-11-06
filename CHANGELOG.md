# Changelog

Mudanças relevantes do CashTrail, por marco. O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), com marcos no lugar de números de versão; cada entrada aponta o documento de desenho com as decisões.

As datas são de conclusão do marco. A coluna "produção" diz quando a entrega foi publicada (os deploys são em lote).

## [Não publicado]

### Marco 17 — Acabamento (em andamento)

[Documento](docs/marcos/33-marco-17-acabamento.md)

- **Adicionado:** navegação em cápsula com o módulo atual em âmbar, gaveta aberta pelo logo com busca ("Ir para uma tela", atalho `/`), as 21 telas agrupadas por módulo.
- **Mudado:** Resumo do mês com um número principal, uma frase, avisos numa lista só, gastos por categoria em barras e navegação entre meses.
- **Removido:** o gráfico "Evolução de saldo" do Resumo (era o resultado acumulado, não o saldo; o calendário mostra o saldo real).
- **Corrigido:** data padrão dos formulários em UTC (depois das 21h sugeria o dia seguinte); datas cruas `AAAA-MM-DD` na tela; evolução do dashboard com um ponto por lançamento em vez de um por dia; e-mail exibido sem função em 7 telas.

### Marco 16 — Redesign — 2026-10-29

[Documento](docs/marcos/32-marco-16-redesign.md)

- **Adicionado:** calendário do dinheiro como tela inicial (saldo de hoje, dia mais apertado, linha de saldo, detalhe do dia) e `GET /reports/calendar`.
- **Adicionado:** tema claro e escuro, seguindo o sistema na primeira visita.
- **Mudado:** identidade visual própria, com cores de dinheiro e de gráficos com contraste AA medido nos dois temas; menu de 6 módulos.
- **Corrigido:** a fonte Geist era carregada e nunca aplicada; `lang` do HTML era `en`.

## Marco 15 — Seguros e independência financeira — 2026-10-15 · produção 2026-10-15

[Documento](docs/marcos/30-marco-15-seguros-e-aposentadoria.md)

- **Adicionado:** apólices com prêmio gerando contas a pagar, alerta de renovação e de bens sem seguro.
- **Adicionado:** simulador de independência financeira em valores reais, com cenários de taxa de retirada × retorno.

## Marco 14 — Imposto de renda — 2026-10-15 · produção 2026-10-15

[Documento](docs/marcos/29-marco-14-irpf.md)

- **Adicionado:** apoio ao IRPF: marca fiscal nas categorias, informes de rendimentos, dependentes, bens em 31/12, estimativa completa × simplificada e apuração mensal de ações e FIIs com DARF.

## Marco 13 — Investimentos — 2026-10-15 · produção 2026-10-15

[Documento](docs/marcos/28-marco-13-investimentos.md)

- **Adicionado:** carteira com compras, vendas e proventos, custo médio, cotações pela brapi, CDI pelo Banco Central e investimentos no balanço.

## Marco 12 — Patrimônio — 2026-10-15 · produção 2026-10-15

[Documento](docs/marcos/27-marco-12-patrimonio-e-balanco.md)

- **Adicionado:** bens com histórico de avaliações, balanço pessoal (ativos − passivos) e evolução mensal do patrimônio.

## Marco 11 — Dívidas e financiamentos — 2026-10-09 · produção 2026-10-15

[Documento](docs/marcos/26-marco-11-dividas-e-financiamentos.md)

- **Adicionado:** empréstimos e financiamentos (Price, SAC, sem juros), baixa separando principal e encargos, quitação e amortização extra com recálculo.

## Marco 10 — Fluxo de caixa e DRE — 2026-10-09 · produção 2026-10-15

[Documento](docs/marcos/25-marco-10-fluxo-de-caixa-e-dre.md)

- **Adicionado:** saldo inicial por conta, grupo de DRE nas categorias, DRE por competência, fluxo de caixa previsto × realizado com projeção, exportação CSV.
- **Corrigido (2026-10-22):** o "período anterior" do DRE compara meses inteiros com meses inteiros (outubro com setembro).

## Marco 9 — Cartões, faturas e transferências — 2026-10-09 · produção 2026-10-15

[Documento](docs/marcos/24-marco-9-cartoes-e-faturas.md)

- **Adicionado:** transferências entre contas, cartões com faturas por ciclo, compras parceladas, pagamento de fatura como transferência, limite.

## Marco 8 — Contas a pagar e a receber — 2026-10-08 · produção 2026-10-15

[Documento](docs/marcos/23-marco-8-contas-a-pagar-receber.md)

- **Adicionado:** compromissos com baixa parcial, parcelamento, situação calculada, alerta de vencimentos; recorrência pode gerar compromisso.

## Marco 7 — Recuperação de senha e importação — 2026-10-08 · produção 2026-10-15

- **Adicionado:** recuperação de senha por e-mail (Azure Communication Services, ligado em 2026-10-22) e importação de extrato CSV com pré-visualização e aviso de duplicatas.
- **Mudado:** agenda do banco em produção.

## Marcos 3 a 6 — MVP — 2026-09-28 · produção 2026-09-28

- **Adicionado:** categorias, lançamentos, dashboard, orçamentos com alerta, metas de economia, recorrências com job agendado.
- **Segurança:** rate limiting no login, proteção CSRF das rotas de cookie, deploy por GitHub Actions com OIDC.

## Marco 2 — Primeira slice e deploy — 2026-09-19 · produção 2026-09-19

- **Adicionado:** cadastro, login e contas; primeiro deploy no Azure Container Apps.

## Marco 1 — Discovery — 2026-09-16

- **Adicionado:** discovery completo (fases 0 a 20), ADRs 001 a 007 e roadmap inicial ([histórico](docs/historico/README.md)).
