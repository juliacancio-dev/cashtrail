# Catálogo de requisitos

Índice único dos identificadores citados no código (`RF-033`, `RB-014`, `RNF-001`...). Cada linha resume o requisito e aponta o documento que o definiu, onde estão o critério de aceitação e o contexto. Para entender as regras em conjunto, leia [Regras de negócio](../produto/regras-de-negocio.md).

| Prefixo | Significa |
|---|---|
| RF | requisito funcional |
| RB | regra de negócio |
| RNF | requisito não funcional |
| SEC | requisito de segurança |
| INT, OPS | integração e operação |
| R-x.y | risco do marco *x* (definido no documento do marco) |

## Colisões de numeração

Dois blocos de IDs foram reutilizados por engano em marcos diferentes, e o código usa os dois significados. **Ao ler um comentário com um destes IDs, olhe a slice para saber qual vale.**

| IDs | Marco 10 (`reports`, `accounts`, `categories`) | Marcos 11 e 12 (`debts`, `commitments`, `reports/net_worth`) |
|---|---|---|
| RF-032 a RF-037 | saldo, DRE e fluxo de caixa | dívidas |
| RB-023 a RB-029 | fluxo de caixa e DRE | dívidas (023–027) e patrimônio (028–029) |

Os RFs do Marco 10 (RF-031 a RF-037) não foram tabelados no documento do marco; as linhas abaixo foram reconstruídas a partir do plano do marco e dos comentários do código. **IDs novos continuam em RF-076 e RB-049.**

## Requisitos funcionais

| ID | Requisito | Origem |
|---|---|---|
| RF-001 | Cadastro com e-mail e senha | [03](../historico/discovery/03-requirements.md) |
| RF-002 | Login com JWT (access + refresh), sem revelar qual campo errou | [03](../historico/discovery/03-requirements.md) |
| RF-003 | CRUD de contas; arquivada não recebe lançamento novo, mantém histórico | [03](../historico/discovery/03-requirements.md) |
| RF-004 | CRUD de categorias; com lançamentos, só arquiva | [03](../historico/discovery/03-requirements.md) |
| RF-005 | CRUD de lançamentos manuais (receita/despesa) | [03](../historico/discovery/03-requirements.md) |
| RF-006 | Dashboard mensal: resumo, gasto por categoria, evolução | [03](../historico/discovery/03-requirements.md) |
| RF-007 | Orçamento por categoria e mês, real × planejado | [03](../historico/discovery/03-requirements.md) |
| RF-008 | Alerta de orçamento ultrapassado (RF-008a: só na tela) | [03](../historico/discovery/03-requirements.md), [12](../historico/discovery/12-mvp.md) |
| RF-009 | Metas de economia com progresso pelos lançamentos vinculados | [03](../historico/discovery/03-requirements.md) |
| RF-010 | Lançamento recorrente com geração automática | [03](../historico/discovery/03-requirements.md) |
| RF-011 | Importação de extrato (só CSV na implementação) | [03](../historico/discovery/03-requirements.md) |
| RF-012 | Prevenção de duplicatas na importação | [03](../historico/discovery/03-requirements.md), [04](../historico/discovery/04-usecases.md) |
| RF-013 | Recuperação de senha por link de uso único e expiração curta | [11](../historico/discovery/11-security.md) |
| RF-014 | CRUD de compromissos a pagar e a receber | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-015 | Parcelamento em N compromissos somando exatamente o total | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-016 | Baixa cria um lançamento realizado | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-017 | Baixa parcial mantém o saldo em aberto | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-018 | Situação calculada (aberto, vence hoje, atrasado, pago, parcial, cancelado) | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-019 | Listagem com filtros e totais | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-020 | Cancelar compromisso sem apagar | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-021 | Alerta de vencimentos no dashboard | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-022 | Recorrência pode gerar compromisso | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RF-023 | Transferência entre contas (criar, listar, desfazer) | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RF-024 | Cadastro de cartão: fechamento, vencimento, limite, conta de pagamento | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RF-025 | Compra no cartão ligada a uma fatura | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RF-026 | Compra parcelada, uma despesa por fatura | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RF-027 | Faturas por ciclo: período, vencimento, total, pago, saldo, situação | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RF-028 | Pagar fatura (total ou parcial) como transferência; desfazer | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RF-029 | Limite usado e disponível | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RF-030 | Alerta de faturas no dashboard | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RF-031 | Saldo inicial por conta e saldo atual | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RF-032 (M10) | Grupo de DRE nas categorias | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RF-033 (M10) | DRE do período com % da receita e período anterior | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RF-034 (M10) | Fluxo de caixa realizado por mês | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RF-035 (M10) | Fluxo de caixa previsto por mês | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RF-036 (M10) | Projeção e detalhe dos itens de cada número | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RF-037 (M10) | Exportação CSV do DRE e do fluxo | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RF-032 (M11) | Cadastrar dívida (principal, parcelas, 1º vencimento, sistema, taxa) | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-033 (M11) | Gerar cronograma (Price, SAC, sem juros, informado) | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-034 (M11) | Editar valor ou vencimento de parcela em aberto | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-035 (M11) | Receber o dinheiro da dívida como transferência | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-036 (M11) | Pagar parcela separando principal e encargos; desfazer | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-037 (M11) | Saldo devedor e resumo da dívida | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-038 | Quitação antecipada | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-039 | Saldo devedor total no dashboard e no fluxo | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-040 | Amortização extra com recálculo | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RF-041 | Cadastrar bem | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RF-042 | Avaliações do bem por data | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RF-043 | Vincular bem a uma dívida | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RF-044 | Balanço patrimonial numa data | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RF-045 | Evolução do patrimônio por mês | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RF-046 | Patrimônio líquido por bem | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RF-047 | Exportar balanço em CSV | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RF-048 | Patrimônio no dashboard | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RF-049 | Conta de investimento e ativos | [28](../marcos/28-marco-13-investimentos.md) |
| RF-050 | Registrar compra | [28](../marcos/28-marco-13-investimentos.md) |
| RF-051 | Registrar venda | [28](../marcos/28-marco-13-investimentos.md) |
| RF-052 | Registrar provento | [28](../marcos/28-marco-13-investimentos.md) |
| RF-053 | Posição e carteira | [28](../marcos/28-marco-13-investimentos.md) |
| RF-054 | Cotação com cache | [28](../marcos/28-marco-13-investimentos.md) |
| RF-055 | Atualizar cotações (botão e job) com teto mensal | [28](../marcos/28-marco-13-investimentos.md) |
| RF-056 | Valor manual (renda fixa, fundo, outro) | [28](../marcos/28-marco-13-investimentos.md) |
| RF-057 | Comparativo com o CDI | [28](../marcos/28-marco-13-investimentos.md) |
| RF-058 | Carteira no balanço patrimonial | [28](../marcos/28-marco-13-investimentos.md) |
| RF-059 | Marca fiscal nas categorias | [29](../marcos/29-marco-14-irpf.md) |
| RF-060 | Dependentes (sem CPF) | [29](../marcos/29-marco-14-irpf.md) |
| RF-061 | Informes de rendimentos | [29](../marcos/29-marco-14-irpf.md) |
| RF-062 | Bens, direitos e dívidas em 31/12 | [29](../marcos/29-marco-14-irpf.md) |
| RF-063 | Estimativa anual: completa × simplificada | [29](../marcos/29-marco-14-irpf.md) |
| RF-064 | Apuração mensal de renda variável | [29](../marcos/29-marco-14-irpf.md) |
| RF-065 | Parâmetros fiscais por ano, com fonte | [29](../marcos/29-marco-14-irpf.md) |
| RF-066 | Exportar o dossiê em CSV | [29](../marcos/29-marco-14-irpf.md) |
| RF-067 | Aviso de limites em toda tela de IRPF | [29](../marcos/29-marco-14-irpf.md) |
| RF-068 | Cadastrar apólice | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RF-069 | Prêmio gera contas a pagar | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RF-070 | Renovar apólice | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RF-071 | Alertas de renovação e bens sem seguro | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RF-072 | Plano de independência financeira | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RF-073 | Patrimônio-alvo, progresso, tempo e aporte necessário | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RF-074 | Cenários de taxa de retirada × retorno | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RF-075 | Seguros e independência no dashboard | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |

## Regras de negócio

| ID | Regra | Origem |
|---|---|---|
| RB-001 | Lançamento pertence a exatamente uma conta e uma categoria | [03](../historico/discovery/03-requirements.md) |
| RB-002 | Um orçamento por categoria e mês, por usuário | [03](../historico/discovery/03-requirements.md) |
| RB-003 | Progresso da meta = soma dos lançamentos vinculados; conta arquivada não recebe lançamento novo | [03](../historico/discovery/03-requirements.md), [10](../historico/discovery/10-data-model.md) |
| RB-004 | Recorrência gera até ser desativada | [03](../historico/discovery/03-requirements.md) |
| RB-005 | Categoria com lançamentos só arquiva | [03](../historico/discovery/03-requirements.md) |
| RB-006 | Critério de possível duplicata na importação; nunca descartar em silêncio | [04](../historico/discovery/04-usecases.md) |
| RB-007 | Baixa a pagar gera despesa; a receber gera receita | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RB-008 | Saldo do compromisso = valor − baixas; pago no zero | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RB-009 | Atrasado é derivado, nunca gravado | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RB-010 | Baixa em conta arquivada é rejeitada | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RB-011 | Baixa nunca ultrapassa o saldo | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RB-012 | Parcelas somam o total; centavos na primeira | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RB-013 | Cancelado ou pago não muda valor nem vencimento | [23](../marcos/23-marco-8-contas-a-pagar-receber.md) |
| RB-014 | Transferência não é receita nem despesa | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RB-015 | Transferência entre contas diferentes, próprias, não arquivadas | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RB-016 | Compra no cartão é despesa na data da compra; pagamento da fatura nunca | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RB-017 | Fatura = compras do ciclo − estornos | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RB-018 | Pagamento maior que o saldo da fatura é rejeitado | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RB-019 | Compra até o fechamento, inclusive, entra na fatura que fecha; fatura movível | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RB-020 | Limite disponível = limite − dívida; ultrapassar só avisa | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RB-021 | Dias 29 a 31 viram o último dia do mês | [24](../marcos/24-marco-9-cartoes-e-faturas.md) |
| RB-022 | DRE por competência; transferências fora | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RB-023 (M10) | Fluxo realizado por caixa; compra no cartão só no pagamento | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RB-024 (M10) | Previsto pelo valor bruto no vencimento | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RB-025 (M10) | Atrasado vira pendente no mês atual da projeção | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RB-026 (M10) | Saldo inicial + entradas − saídas = saldo final; fórmula do saldo da conta | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RB-027 (M10) | Projeção não inclui compras futuras não lançadas | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RB-028 (M10) | Categoria sem grupo cai em "Sem grupo" | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RB-029 (M10) | Lançamento no sentido oposto abate o grupo | [25](../marcos/25-marco-10-fluxo-de-caixa-e-dre.md) |
| RB-023 (M11) | Receber empréstimo e amortizar principal não são receita nem despesa | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RB-024 (M11) | Encargos são despesa financeira | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RB-025 (M11) | Parcela paga não é editada, só desfeita | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RB-026 (M11) | Saldo devedor nunca negativo | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RB-027 (M11) | Recálculo só altera parcelas em aberto | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| RB-028 (M12) | Patrimônio líquido = caixa + bens − cartões − dívidas | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RB-029 (M12) | Transferências e pagamentos não mudam o patrimônio por si só | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RB-030 | Bem vale zero antes da primeira avaliação | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RB-031 | Balanço de uma data usa só movimentos até ela | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| RB-032 | Patrimônio usa valor de mercado; saldo da conta `investment` fica fora | [28](../marcos/28-marco-13-investimentos.md) |
| RB-033 | Compra e aporte são transferências | [28](../marcos/28-marco-13-investimentos.md) |
| RB-034 | Ganho na venda = produto − custo médio × quantidade | [28](../marcos/28-marco-13-investimentos.md) |
| RB-035 | Provento é receita financeira; não reduz o custo | [28](../marcos/28-marco-13-investimentos.md) |
| RB-036 | Custo médio ponderado móvel, com taxas | [28](../marcos/28-marco-13-investimentos.md) |
| RB-037 | Valorização não realizada não entra no DRE | [28](../marcos/28-marco-13-investimentos.md) |
| RB-038 | Ganho de renda variável fora da base anual | [29](../marcos/29-marco-14-irpf.md) |
| RB-039 | Vendas de ações até R$ 20 mil no mês: isento no mês | [29](../marcos/29-marco-14-irpf.md) |
| RB-040 | Prejuízo compensa só a mesma modalidade, acumulando | [29](../marcos/29-marco-14-irpf.md) |
| RB-041 | Bens e direitos pelo custo | [29](../marcos/29-marco-14-irpf.md) |
| RB-042 | Parâmetros fiscais versionados por ano | [29](../marcos/29-marco-14-irpf.md) |
| RB-043 | Nenhum CPF/CNPJ de terceiro armazenado | [29](../marcos/29-marco-14-irpf.md) |
| RB-044 | Prêmio é despesa do período | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RB-045 | Simulação em valores reais | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RB-046 | Patrimônio-alvo = (renda − benefício) × 12 ÷ taxa de retirada | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RB-047 | Progresso usa só investimentos, salvo escolha | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| RB-048 | Retirada e retorno são premissas do usuário | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |

## Não funcionais, segurança, integração e operação

| ID | Requisito | Situação |
|---|---|---|
| RNF-001 | Isolamento de dados por usuário, com teste dedicado | Atendido: teste de isolamento em cada slice |
| RNF-002 | Senha com hash forte | Atendido: Argon2 |
| RNF-003, RNF-004 | Tempo de resposta e disponibilidade | Sem meta definida (sem volume real que a justifique) |
| RNF-005 | Testes nos fluxos críticos | Atendido: mais de 700 testes de backend contra PostgreSQL real |
| RNF-006 | Custo dentro do crédito Azure for Students | Acompanhado; ver [deploy e operação](../guias/deploy-e-operacao.md#custo) |
| SEC-001 | Access token curto + refresh token | Atendido: 15 min / 30 dias |
| SEC-002 | Toda consulta filtra por `user_id` | Atendido |
| SEC-003 | Validação Pydantic em toda rota | Atendido |
| SEC-004 | Upload com limite de tamanho, tipo e parsing isolado | Atendido |
| SEC-005 | Segredos fora do código | Atendido (Key Vault sem referência viva; ver [segurança](../arquitetura/seguranca.md#lacunas-conhecidas)) |
| SEC-006 | Rate limiting no login | Atendido |
| INT-001 | Armazenar extratos importados | Descartado: o arquivo não é guardado |
| INT-002 | Integração bancária (Open Finance) | Fora do escopo por custo |
| OPS-001 | CI com testes a cada push e PR | Atendido: `ci.yml` |
| OPS-002 | Docker e deploy reproduzível | Atendido: `deploy.yml` |
| OPS-003 | Migrações versionadas | Atendido: Alembic |
| OPS-004 | Logs mínimos em produção | Atendido: *Log stream* |

## Riscos citados no código

| ID | Risco | Origem |
|---|---|---|
| R-009 | Retenção do backup não confirmada (fechado: 7 dias) | [15](../historico/discovery/15-risks.md) |
| R-11.1 | `ALTER TYPE ... ADD VALUE` em migração | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| R-11.3 | "Conta de caixa" precisa excluir `loan` (e depois `investment`): um único predicado, `NON_CASH_TYPES` | [26](../marcos/26-marco-11-dividas-e-financiamentos.md) |
| R-12.1 | Avaliação de bem desatualizada distorce o patrimônio (mostrar a data da última avaliação) | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| R-12.3 | Saldo inicial é "de hoje para trás": meses anteriores ao uso mostram só o saldo inicial | [27](../marcos/27-marco-12-patrimonio-e-balanco.md) |
| R-13.5 | Cotação desatualizada passa despercebida (mostrar a data e avisar após 3 dias úteis) | [28](../marcos/28-marco-13-investimentos.md) |
| R-15.3 | Prêmio duplicado entre recorrência e conta a pagar (a apólice é a única origem) | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
| R-15.5 | Dado sensível de seguro: só metadados, sem número de apólice nem documentos | [30](../marcos/30-marco-15-seguros-e-aposentadoria.md) |
