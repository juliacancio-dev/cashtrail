# CashTrail — Requisitos (FASE 3)

> Prioridade: **Alta** (MVP, ver `05-mvp.md`), **Média** (importante, adiável), **Baixa** (stretch).
> Onde uma métrica não pôde ser definida com informação real, o campo diz "decisão pendente" em vez de um número inventado.

## Decisões de escopo tomadas nesta fase
- **Metas de economia**: progresso calculado a partir de lançamentos vinculados à meta (não aporte manual). Implica que um lançamento pode, opcionalmente, referenciar uma meta.
- **Importação de extrato**: CSV e OFX suportados desde o MVP.

---

## RF — Requisitos Funcionais

| ID | Descrição | Origem | Prioridade | Critério de aceitação |
|---|---|---|---|---|
| RF-001 | Usuário pode se registrar com e-mail e senha | FASE 1 (decisão multi-user) | Alta | Registro cria usuário com senha em hash; e-mail duplicado é rejeitado |
| RF-002 | Usuário pode fazer login e receber JWT (access + refresh) | FASE 1 | Alta | Login com credenciais corretas retorna tokens válidos; credenciais erradas retornam erro sem detalhar qual campo falhou (evita enumeração de e-mail) |
| RF-003 | CRUD de contas (corrente, poupança, cartão de crédito) | Dor "contas espalhadas" | Alta | Usuário cria, edita, arquiva conta; conta arquivada não aparece em novos lançamentos mas mantém histórico |
| RF-004 | CRUD de categorias de lançamento | Dor "não sei pra onde vai o dinheiro" | Alta | Usuário cria/edita/remove categoria; categoria com lançamentos associados não pode ser excluída (ver RB-005) |
| RF-005 | CRUD de lançamentos manuais (receita/despesa) | Dor "não sei pra onde vai o dinheiro" | Alta | Lançamento exige conta, categoria, valor, data; aparece no dashboard imediatamente |
| RF-006 | Dashboard mensal (resumo, gasto por categoria, evolução de saldo) | Dor "contas espalhadas" / "não sei pra onde vai" | Alta | Soma exibida bate com soma manual dos lançamentos do período (critério de verificação da Fase 2 do roadmap) |
| RF-007 | CRUD de orçamento por categoria/mês com acompanhamento real vs. planejado | Dor "não consigo planejar" | Alta | Orçamento mostra % consumido em tempo real conforme lançamentos são criados |
| RF-008 | Alerta quando orçamento é ultrapassado | Dor "não consigo planejar" | Média | Ao lançar despesa que ultrapassa o limite da categoria/mês, sistema sinaliza (mecanismo exato — ver RF-008a) |
| RF-008a | Mecanismo do alerta (in-app vs. e-mail) | — | — | **Decisão pendente** — endereçar em `05-mvp.md` |
| RF-009 | CRUD de metas de economia, com progresso derivado de lançamentos vinculados | Dor "não consigo poupar" | Alta | Meta mostra % atingido = soma dos lançamentos vinculados / valor alvo |
| RF-010 | Lançamento recorrente (assinatura/conta fixa) — criação e geração automática | Dor "esqueço de contas fixas" | Alta | Lançamento recorrente configurado gera automaticamente o lançamento do período seguinte sem ação manual |
| RF-011 | Importação de extrato bancário em CSV e OFX | Dor "contas espalhadas" | Média | Upload de arquivo válido cria lançamentos correspondentes; arquivo inválido é rejeitado com mensagem clara |
| RF-012 | Prevenção de lançamento duplicado na importação | Decorre de RF-011 + RF-010 | Média | Reimportar o mesmo arquivo não cria lançamentos duplicados (critério de verificação exato a definir na FASE 4 — fluxos) |

## RNF — Requisitos Não Funcionais

| ID | Descrição | Prioridade | Observação |
|---|---|---|---|
| RNF-001 | Isolamento de dados por usuário (nenhum usuário acessa dado de outro) | Alta | Validar com teste automatizado dedicado, não só revisão manual |
| RNF-002 | Senhas armazenadas com hash forte (bcrypt ou argon2), nunca em texto puro | Alta | — |
| RNF-003 | Tempo de resposta da API sob carga normal | — | **Decisão pendente** — sem volume de uso real conhecido ainda para definir um número verificável; não inventar um SLA agora |
| RNF-004 | Disponibilidade do serviço | — | **Decisão pendente** — mesmo motivo do RNF-003; projeto de portfólio/uso pessoal não justifica SLA formal ainda |
| RNF-005 | Cobertura de testes automatizados nos fluxos críticos (auth, lançamentos, orçamento, metas) | Alta | Meta de cobertura % — decisão pendente para `09-estimates.md`, não travar agora em número arbitrário |
| RNF-006 | Custo de infraestrutura dentro do crédito/free tier do Azure for Students | Alta | Depende da validação oficial de limites (FASE 6) |

## RB — Regras de Negócio

| ID | Descrição | Dependência |
|---|---|---|
| RB-001 | Todo lançamento pertence a exatamente uma conta e uma categoria | RF-003, RF-004, RF-005 |
| RB-002 | Não pode existir mais de um orçamento para o mesmo par categoria+mês/ano, por usuário | RF-007 |
| RB-003 | Progresso de meta = soma dos lançamentos vinculados a ela (RF-009) | RF-009, RF-005 |
| RB-004 | Lançamento recorrente continua gerando lançamentos futuros até ser cancelado ou editado pelo usuário | RF-010 |
| RB-005 | Categoria com lançamentos associados não pode ser excluída (só arquivada) | RF-004 |
| RB-006 | Critério de "correspondência" para evitar duplicidade na importação (RF-012) | **Decisão pendente** — precisa ser definido na FASE 4 (ex: mesma data + valor + conta = provável duplicata) |

## SEC — Requisitos de Segurança

| ID | Descrição | Risco mitigado |
|---|---|---|
| SEC-001 | JWT com access token de vida curta + refresh token | Reduz janela de uso de token vazado |
| SEC-002 | Toda query de dados filtra por `user_id` do token autenticado | Vazamento de dados entre usuários |
| SEC-003 | Validação de entrada via Pydantic em todos os endpoints | Dados malformados / injeção |
| SEC-004 | Upload de extrato: limite de tamanho de arquivo, validação de tipo/extensão, parsing isolado de erro | Upload malicioso / DoS por arquivo grande |
| SEC-005 | Segredos (DB, JWT secret) fora do código-fonte — variáveis de ambiente / Azure Key Vault | Vazamento de credenciais no repositório público |
| SEC-006 | Rate limiting no endpoint de login | Força bruta de senha |

## INT — Requisitos de Integração

| ID | Descrição | Status |
|---|---|---|
| INT-001 | Armazenamento de arquivos de extrato importados | Serviço exato (Azure Blob Storage provavelmente) a confirmar na FASE 7 (stack)/FASE 8 (arquitetura) |
| INT-002 | Integração bancária real via Open Finance (agregador tipo Pluggy/Belvo) | Fora do MVP — custo (R$2,5k-6k/mês) inviável hoje, ver `02-market-research.md`. Mantido só como restrição de modelagem de dados, não como entrega planejada |

## OPS — Requisitos Operacionais

| ID | Descrição |
|---|---|
| OPS-001 | CI executa build + testes automatizados em cada push/PR |
| OPS-002 | Aplicação empacotada em Docker, deploy reproduzível |
| OPS-003 | Migrations de banco versionadas (Alembic) |
| OPS-004 | Logs estruturados mínimos para depuração em produção |

---

**STATUS**: Pronto para avançar, com pendências explícitas (não bloqueantes):
- RF-008a (mecanismo de alerta) → resolver em `05-mvp.md`
- RB-006 (critério de duplicidade) → resolver na FASE 4 (casos de uso/fluxos)
- RNF-003/004/005 (métricas de performance/disponibilidade/cobertura) → resolver quando houver base para números reais, não antes

Seguimos para a **FASE 4 — Casos de Uso e Fluxos** (incluindo o fluxo de conciliação de importação, que resolve o RB-006 pendente)?
