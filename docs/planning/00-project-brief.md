# CashTrail — Project Brief

## Ideia original
Plataforma de gestão financeira pessoal, construída para uso real da autora (Julia) e para ser a peça central do portfólio técnico no GitHub (`juliacancio-dev`).

## Duplo problema (não confundir os dois)
- **Problema A (produto)**: falta de controle/visibilidade consolidada sobre a vida financeira pessoal.
- **Problema B (motor real do projeto)**: o portfólio de Julia não demonstrava, até este projeto, competência técnica atual (API real, testes, deploy em nuvem).

O Problema A foi escolhido como veículo para resolver o Problema B — isso não desvaloriza o Problema A (é uma dor real e confirmada), mas explica por que certas decisões (ex: capricho em CI/CD e deploy) pesam mais do que normalmente pesariam num side-project de uso puramente pessoal.

## Objetivo
- Ter, pela primeira vez, controle estruturado da própria vida financeira (hoje: nenhum controle organizado).
- Produzir um projeto de portfólio que prove, com evidência real (testes, CI, deploy), a stack usada no dia a dia profissional (Python) mais frontend moderno.

## Decisões fundamentais já tomadas
| Decisão | Escolha | Registrada em |
|---|---|---|
| Domínio | Gestão financeira pessoal | FASE 0 |
| Nome | CashTrail | — |
| Backend | Python + FastAPI | prompt padrão de stack |
| Frontend | Next.js + shadcn/ui | prompt padrão de stack |
| Banco | PostgreSQL | prompt padrão de stack |
| Cloud | **Azure** (substituiu decisão anterior de AWS) | FASE 0 |
| Modelo de usuário | Multi-user desde o início (auth JWT, `user_id` isolando dados) | FASE 1 |
| Integração bancária real | Fora do MVP; modelo de dados deixa espaço, mas tratada como aspiração distante (ver `02-market-research.md`) | FASE 0 / FASE 2 |
| Uso real | Sim — Julia pretende usar de verdade, não é só demo | FASE 0 |
| Prazo-alvo | Nenhum definido | FASE 0 |
| Orçamento cloud | Azure for Students (créditos a validar oficialmente) | FASE 0 |

## Restrições
- Nenhuma sobreposição com o trabalho confidencial da Julia na Greystar (nem o domínio, nem qualquer lógica/UX inspirada nele).
- Repositório mantido fora do OneDrive corporativo.

## Como usar este documento
Este brief é o resumo executivo. Detalhes de cada fase do discovery estão nos documentos seguintes desta pasta (`docs/`). Atualize este arquivo sempre que uma decisão fundamental mudar.
