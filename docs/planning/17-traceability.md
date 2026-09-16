# CashTrail — Traceabilidade (FASE 17)

Objetivo → Problema → Requisito → Slice → Marco → Critério de aceitação

| Objetivo | Problema (dor) | Requisitos | Slice | Marco | Critério de aceitação |
|---|---|---|---|---|---|
| Controle de acesso seguro | Base para tudo (uso real multi-user) | RF-001, RF-002, RNF-001, RNF-002, SEC-001/002/006 | `auth` | Marco 2 | Registro/login funcionam; teste de isolamento por usuário passa |
| Visão consolidada de contas | "Contas/cartões espalhados" | RF-003 | `accounts` | Marco 2 | CRUD de conta funcional, conta arquivada preserva histórico |
| Visibilidade por categoria | "Não sei pra onde vai o dinheiro" | RF-004, RF-005 | `categories`, `transactions` | Marco 3 | Lançamento categorizado aparece corretamente agregado |
| Visão consolidada de gastos | "Contas/cartões espalhados" + "não sei pra onde vai" | RF-006 | `dashboard` | Marco 3 | Dashboard bate com conferência manual |
| Planejamento financeiro | "Não consigo poupar/planejar" | RF-007, RF-008 | `budgets` | Marco 4 | % consumido reflete lançamentos em tempo real |
| Metas de economia | "Não consigo poupar/planejar" | RF-009 | `goals` | Marco 4 | Progresso = soma de lançamentos vinculados |
| Não esquecer contas fixas | "Esqueço de contas fixas/assinaturas" | RF-010 | `recurring` | Marco 5 | Lançamento futuro gerado automaticamente sem ação manual |
| Prova de produção real (portfólio) | Problema B (portfólio sem prova técnica) | OPS-001/002/003/004 | infraestrutura transversal (`core/`) | Marco 6 | CI verde, deploy acessível publicamente |
| Consolidação sem digitação manual | "Contas/cartões espalhados" (conveniência) | RF-011, RF-012 | `statement_import` | Marco 7 | Reimportar o mesmo arquivo não duplica lançamentos |
| Continuidade de uso real | Uso real contínuo (não só demo) | RF-013 | `auth` (extensão) | Marco 7 | Fluxo de recuperação de senha funciona ponta a ponta |

**Como usar esta tabela**: ao implementar qualquer slice, confirme que o requisito relacionado está sendo atendido e que existe teste cobrindo o critério de aceitação — nenhuma linha de código deveria existir sem estar rastreável até uma dessas linhas.

---

**STATUS**: Pronto para avançar.
