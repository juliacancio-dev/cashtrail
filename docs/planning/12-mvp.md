# CashTrail — Definição do MVP (FASE 12)

## Decisões que fecham pendências das fases anteriores

**RF-008a (mecanismo de alerta de orçamento estourado)**: resolvido como **alerta in-app apenas** no MVP (sem e-mail). Justificativa: e-mail transacional só está sendo introduzido para RF-013 (recuperação de senha, fluxo crítico); usar o mesmo canal para alertas não-críticos (orçamento estourado) pode esperar uma iteração posterior sem prejuízo real — você vê o alerta assim que abre o dashboard.

**Serviço de e-mail para RF-013**: **Azure Communication Services Email** (decisão sua) — mantém tudo num único fornecedor, custo irrisório no volume esperado (poucos e-mails/ano).

## Objetivo do MVP

Entregar, de ponta a ponta, o ciclo completo de controle financeiro **manual** (contas → categorias → lançamentos → dashboard → orçamento → metas → recorrência), com autenticação real multiusuário — provando simultaneamente que a dor central (nenhum controle estruturado hoje) é resolvida e que a stack técnica (auth, testes, deploy) funciona de verdade.

**Menor versão capaz de provar que o problema central está sendo resolvido**: você consegue abrir o app, registrar todas as suas contas e lançamentos do mês, ver quanto gastou por categoria, saber se estourou o orçamento e acompanhar uma meta — sem precisar de planilha nem "cabeça".

## Usuário-alvo do MVP

Você (usuária real confirmada). Não há usuário secundário no MVP.

## Funcionalidades obrigatórias (dentro do MVP)

| RF | Funcionalidade |
|---|---|
| RF-001, RF-002 | Registro e login (JWT) |
| RF-003 | CRUD de contas |
| RF-004 | CRUD de categorias |
| RF-005 | Lançamentos manuais |
| RF-006 | Dashboard mensal |
| RF-007, RF-008 | Orçamento por categoria/mês + alerta in-app |
| RF-009 | Metas de economia (progresso vinculado a lançamentos) |
| RF-010 | Lançamento recorrente |

## Funcionalidades importantes, mas adiáveis (MVP+1 — não bloqueiam considerar o MVP "pronto")

| RF | Funcionalidade | Por que fica de fora do MVP inicial |
|---|---|---|
| RF-011, RF-012 | Importação de extrato CSV/OFX | É a slice mais complexa (parsing + conciliação); não é estritamente necessária pra provar o ciclo central — lançamento manual já resolve a dor "não sei pra onde vai o dinheiro" e "contas espalhadas" |
| RF-013 | Recuperação de senha | Importante pra uso contínuo real, mas não bloqueia a primeira entrega demonstrável (você pode redefinir senha manualmente enquanto é a única usuária) — deve entrar logo depois, antes de depender 100% do app no dia a dia |

## Explicitamente fora do MVP (não é objetivo próximo)

- INT-002 — integração bancária real (Open Finance) — inviável por custo/regulação (ver `02-market-research.md`)
- MFA, WAF, log de auditoria completo — deliberadamente fora por desproporção (ver `11-security.md`)
- Multi-moeda, multi-usuário compartilhado (ex: dividir conta com parceiro) — não fazem parte do escopo discutido

## Integrações obrigatórias no MVP

**Nenhuma integração externa real.** Isso é uma característica desejável do MVP, não uma limitação: reduz risco e dependência externa na primeira entrega. E-mail (RF-013) e import (RF-011/012) — as únicas integrações do produto — ficam para depois do MVP.

## Métricas de sucesso

- Você usa o app continuamente por pelo menos 2-4 semanas registrando lançamentos reais, sem voltar a "nada estruturado".
- O valor do dashboard bate com uma conferência manual dos lançamentos do período (critério de verificação já previsto no roadmap original).
- CI verde a cada push; suite de testes cobre os fluxos críticos (auth, isolamento por usuário, orçamento, meta).
- Aplicação acessível publicamente via URL (não só rodando local).

## Critérios de aceitação do MVP (visão de conjunto)

O MVP está pronto quando: todas as 8 funcionalidades obrigatórias estão implementadas e testadas; autenticação e isolamento por usuário têm teste dedicado (RNF-001); CI/CD funcional; aplicação deployada e acessível; README do repositório documenta arquitetura, decisões e link de demo.
(Definition of Done detalhado por Vertical Slice será formalizado na FASE 22/23 da metodologia, após o backlog.)

## Riscos específicos do MVP

| Risco | Impacto | Mitigação |
|---|---|---|
| Cold start do Azure Container Apps incomodar o uso diário | Médio — atrito na experiência real de uso | Validar na prática após deploy da primeira slice; App Service fica como alternativa se o cold start for inaceitável |
| SPIKE do Next.js híbrido no Static Web Apps ainda não executado | Médio — pode forçar troca para Vercel no meio do caminho | Executar o SPIKE antes de finalizar o deploy do frontend, não depois |
| Custo do banco sempre ligado, sem automação de start/stop | Baixo/gerenciável — só afeta orçamento, não funcionalidade | Endereçado na FASE 4 do roadmap (Hardening), não bloqueia o MVP funcional |

## Como validar o MVP

Uso real, por você, durante 2-4 semanas após o deploy — comparando a experiência com o "nada estruturado" de hoje. Esse é o teste de validação mais honesto disponível, já que você é a única usuária confirmada; não faz sentido inventar uma validação de mercado que essa fase do projeto não tem.

---

**STATUS**: Pronto para avançar.

Seguimos para a **FASE 13 — Roadmap** (fases, dependências, marcos — agora com MVP e stack já fechados)?
