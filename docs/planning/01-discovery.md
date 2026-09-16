# CashTrail — Discovery (FASE 0 + FASE 1)

> Legenda: **FATO** (informado/comprovado) · **HIPÓTESE** (acreditamos, não validado) · **INFERÊNCIA** (conclusão derivada) · **DESCONHECIDO** (falta informação)

## FASE 0 — Mapa do problema

### Problema
Há dois problemas distintos sobrepostos — ver `00-project-brief.md`.

### Quem possui o problema
- **FATO**: Julia é a dona do Problema A (nenhum controle financeiro estruturado hoje) e do Problema B (portfólio sem prova técnica atual).

### Quem usará / administrará / será afetado
- **FATO**: Julia é usuária confirmada, com intenção real de uso contínuo (não só demo).
- Administração: self-service, sem papel de admin separado.
- Afetados indiretamente: recrutadores avaliam o artefato (repositório/demo), mas não são usuários do sistema.

### Processo atual
- **FATO**: nenhum controle estruturado hoje (nem planilha, nem app dedicado).

### Objetivos
- Negócio: fortalecer o portfólio / empregabilidade.
- Produto: controle financeiro real e contínuo.
- Técnico: demonstrar API real, testes automatizados, CI/CD, deploy em nuvem, modelagem relacional.

### Restrições e dependências
- Ver `00-project-brief.md`.
- **DESCONHECIDO** (a validar na fase de custos): limites exatos do Azure for Students.

### Decisões e perguntas respondidas na FASE 0
| Pergunta | Resposta |
|---|---|
| Uso real ou só demo? | Uso real, dia a dia |
| Cloud: AWS ou Azure? | Azure |
| Integração bancária real no escopo? | Não no MVP; modelo de dados deve deixar espaço para o futuro |
| Prazo-alvo? | Nenhum |
| Processo atual de controle financeiro? | Nenhum (nada estruturado) |
| Orçamento de nuvem? | Azure for Students |

---

## FASE 1 — Product Discovery

### Dores confirmadas (todas relevantes, nenhuma descartada — usuária marcou as 4)
1. Não sabe para onde vai o dinheiro (falta de visibilidade por categoria)
2. Contas/cartões espalhados sem visão consolidada
3. Esquece de contas fixas/assinaturas (sem rastreio de recorrência)
4. Não consegue poupar/planejar metas (sem orçamento estruturado)

Isso confirma que o MVP precisa cobrir as 4 frentes — não há espaço para cortar uma delas sem perder cobertura de uma dor real.

### Decisão de arquitetura nascida da Discovery
**Multi-user desde o início.** Mesmo com um único usuário real confirmado hoje (Julia), o sistema terá autenticação completa (registro/login, JWT) com `user_id` isolando dados em todas as tabelas.
- **Por quê**: custo de implementar agora é baixo; retrofitar depois (ex: se quiser convidar um parceiro) seria caro e arriscado; além disso, autenticação/autorização correta é uma das provas técnicas mais visíveis num portfólio.
- **Confiança**: alta.

### Jornadas principais (hipóteses de fluxo, a refinar na FASE 4 — Casos de Uso)
1. Registro/login (JWT)
2. Cadastrar contas (corrente, poupança, cartão de crédito)
3. Lançar receita/despesa manualmente, categorizada
4. Ver dashboard mensal (resumo, gasto por categoria, evolução de saldo)
5. Criar orçamento por categoria/mês e acompanhar real vs. planejado
6. Criar e acompanhar meta de economia
7. Configurar lançamento recorrente (assinatura/conta fixa)
8. Importar extrato (CSV/OFX) e conciliar com lançamentos existentes

### Eventos de domínio identificados
UsuárioRegistrado, ContaCriada, LançamentoCriado, LançamentoCategorizado, LançamentoRecorrenteGerado, OrçamentoDefinido, OrçamentoEstourado, MetaCriada, MetaAtingida, ExtratoImportado, LançamentoDuplicadoDetectado.

### Entradas / saídas
- Entradas: dados de cadastro, lançamentos manuais, arquivos CSV/OFX.
- Saídas: dashboard, relatórios por categoria/mês, alertas de orçamento estourado.
- **DESCONHECIDO**: mecanismo de alerta (in-app vs. e-mail) — decisão adiada para a FASE do MVP.

### Estados relevantes
Lançamento (confirmado), Meta (em andamento / atingida), Orçamento (dentro do limite / estourado), Conta (ativa / arquivada).

### Pontos de decisão adiados (não bloqueiam o discovery atual)
- Comportamento ao estourar orçamento (só alerta visual vs. notificação ativa) → FASE 12 (MVP).
- Prevenção de duplicidade entre lançamento manual e lançamento importado → FASE 4 (fluxos) e FASE 10 (modelo de dados).

### Exceções previstas
Arquivo de importação malformado; duplicidade de lançamento importado; categoria removida com lançamentos associados.

### Personas
Decisão deliberada de **não** criar personas elaboradas — há uma única usuária real confirmada (Julia). Personas fictícias adicionais seriam documentação de fachada sem utilidade. Revisitar se o produto ganhar múltiplos usuários reais.

---

**GATE 1 (Problema): aprovado.** Problema, usuária e objetivo claros o suficiente para avançar.
