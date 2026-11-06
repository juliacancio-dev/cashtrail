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
| RF-001 | Cadastro com e-mail e senha | discovery 03 |
| RF-002 | Login com JWT (access + refresh), sem revelar qual campo errou | discovery 03 |
| RF-003 | CRUD de contas; arquivada não recebe lançamento novo, mantém histórico | discovery 03 |
| RF-004 | CRUD de categorias; com lançamentos, só arquiva | discovery 03 |
| RF-005 | CRUD de lançamentos manuais (receita/despesa) | discovery 03 |
| RF-006 | Dashboard mensal: resumo, gasto por categoria, evolução | discovery 03 |
| RF-007 | Orçamento por categoria e mês, real × planejado | discovery 03 |
| RF-008 | Alerta de orçamento ultrapassado (RF-008a: só na tela) | discovery 03, discovery 12 |
| RF-009 | Metas de economia com progresso pelos lançamentos vinculados | discovery 03 |
| RF-010 | Lançamento recorrente com geração automática | discovery 03 |
| RF-011 | Importação de extrato (só CSV na implementação) | discovery 03 |
| RF-012 | Prevenção de duplicatas na importação | discovery 03, discovery 04 |
| RF-013 | Recuperação de senha por link de uso único e expiração curta | discovery 11 |
| RF-014 | CRUD de compromissos a pagar e a receber | Marco 8 |
| RF-015 | Parcelamento em N compromissos somando exatamente o total | Marco 8 |
| RF-016 | Baixa cria um lançamento realizado | Marco 8 |
| RF-017 | Baixa parcial mantém o saldo em aberto | Marco 8 |
| RF-018 | Situação calculada (aberto, vence hoje, atrasado, pago, parcial, cancelado) | Marco 8 |
| RF-019 | Listagem com filtros e totais | Marco 8 |
| RF-020 | Cancelar compromisso sem apagar | Marco 8 |
| RF-021 | Alerta de vencimentos no dashboard | Marco 8 |
| RF-022 | Recorrência pode gerar compromisso | Marco 8 |
| RF-023 | Transferência entre contas (criar, listar, desfazer) | Marco 9 |
| RF-024 | Cadastro de cartão: fechamento, vencimento, limite, conta de pagamento | Marco 9 |
| RF-025 | Compra no cartão ligada a uma fatura | Marco 9 |
| RF-026 | Compra parcelada, uma despesa por fatura | Marco 9 |
| RF-027 | Faturas por ciclo: período, vencimento, total, pago, saldo, situação | Marco 9 |
| RF-028 | Pagar fatura (total ou parcial) como transferência; desfazer | Marco 9 |
| RF-029 | Limite usado e disponível | Marco 9 |
| RF-030 | Alerta de faturas no dashboard | Marco 9 |
| RF-031 | Saldo inicial por conta e saldo atual | Marco 10 |
| RF-032 (M10) | Grupo de DRE nas categorias | Marco 10 |
| RF-033 (M10) | DRE do período com % da receita e período anterior | Marco 10 |
| RF-034 (M10) | Fluxo de caixa realizado por mês | Marco 10 |
| RF-035 (M10) | Fluxo de caixa previsto por mês | Marco 10 |
| RF-036 (M10) | Projeção e detalhe dos itens de cada número | Marco 10 |
| RF-037 (M10) | Exportação CSV do DRE e do fluxo | Marco 10 |
| RF-032 (M11) | Cadastrar dívida (principal, parcelas, 1º vencimento, sistema, taxa) | Marco 11 |
| RF-033 (M11) | Gerar cronograma (Price, SAC, sem juros, informado) | Marco 11 |
| RF-034 (M11) | Editar valor ou vencimento de parcela em aberto | Marco 11 |
| RF-035 (M11) | Receber o dinheiro da dívida como transferência | Marco 11 |
| RF-036 (M11) | Pagar parcela separando principal e encargos; desfazer | Marco 11 |
| RF-037 (M11) | Saldo devedor e resumo da dívida | Marco 11 |
| RF-038 | Quitação antecipada | Marco 11 |
| RF-039 | Saldo devedor total no dashboard e no fluxo | Marco 11 |
| RF-040 | Amortização extra com recálculo | Marco 11 |
| RF-041 | Cadastrar bem | Marco 12 |
| RF-042 | Avaliações do bem por data | Marco 12 |
| RF-043 | Vincular bem a uma dívida | Marco 12 |
| RF-044 | Balanço patrimonial numa data | Marco 12 |
| RF-045 | Evolução do patrimônio por mês | Marco 12 |
| RF-046 | Patrimônio líquido por bem | Marco 12 |
| RF-047 | Exportar balanço em CSV | Marco 12 |
| RF-048 | Patrimônio no dashboard | Marco 12 |
| RF-049 | Conta de investimento e ativos | Marco 13 |
| RF-050 | Registrar compra | Marco 13 |
| RF-051 | Registrar venda | Marco 13 |
| RF-052 | Registrar provento | Marco 13 |
| RF-053 | Posição e carteira | Marco 13 |
| RF-054 | Cotação com cache | Marco 13 |
| RF-055 | Atualizar cotações (botão e job) com teto mensal | Marco 13 |
| RF-056 | Valor manual (renda fixa, fundo, outro) | Marco 13 |
| RF-057 | Comparativo com o CDI | Marco 13 |
| RF-058 | Carteira no balanço patrimonial | Marco 13 |
| RF-059 | Marca fiscal nas categorias | Marco 14 |
| RF-060 | Dependentes (sem CPF) | Marco 14 |
| RF-061 | Informes de rendimentos | Marco 14 |
| RF-062 | Bens, direitos e dívidas em 31/12 | Marco 14 |
| RF-063 | Estimativa anual: completa × simplificada | Marco 14 |
| RF-064 | Apuração mensal de renda variável | Marco 14 |
| RF-065 | Parâmetros fiscais por ano, com fonte | Marco 14 |
| RF-066 | Exportar o dossiê em CSV | Marco 14 |
| RF-067 | Aviso de limites em toda tela de IRPF | Marco 14 |
| RF-068 | Cadastrar apólice | Marco 15 |
| RF-069 | Prêmio gera contas a pagar | Marco 15 |
| RF-070 | Renovar apólice | Marco 15 |
| RF-071 | Alertas de renovação e bens sem seguro | Marco 15 |
| RF-072 | Plano de independência financeira | Marco 15 |
| RF-073 | Patrimônio-alvo, progresso, tempo e aporte necessário | Marco 15 |
| RF-074 | Cenários de taxa de retirada × retorno | Marco 15 |
| RF-075 | Seguros e independência no dashboard | Marco 15 |

## Regras de negócio

| ID | Regra | Origem |
|---|---|---|
| RB-001 | Lançamento pertence a exatamente uma conta e uma categoria | discovery 03 |
| RB-002 | Um orçamento por categoria e mês, por usuário | discovery 03 |
| RB-003 | Progresso da meta = soma dos lançamentos vinculados; conta arquivada não recebe lançamento novo | discovery 03, discovery 10 |
| RB-004 | Recorrência gera até ser desativada | discovery 03 |
| RB-005 | Categoria com lançamentos só arquiva | discovery 03 |
| RB-006 | Critério de possível duplicata na importação; nunca descartar em silêncio | discovery 04 |
| RB-007 | Baixa a pagar gera despesa; a receber gera receita | Marco 8 |
| RB-008 | Saldo do compromisso = valor − baixas; pago no zero | Marco 8 |
| RB-009 | Atrasado é derivado, nunca gravado | Marco 8 |
| RB-010 | Baixa em conta arquivada é rejeitada | Marco 8 |
| RB-011 | Baixa nunca ultrapassa o saldo | Marco 8 |
| RB-012 | Parcelas somam o total; centavos na primeira | Marco 8 |
| RB-013 | Cancelado ou pago não muda valor nem vencimento | Marco 8 |
| RB-014 | Transferência não é receita nem despesa | Marco 9 |
| RB-015 | Transferência entre contas diferentes, próprias, não arquivadas | Marco 9 |
| RB-016 | Compra no cartão é despesa na data da compra; pagamento da fatura nunca | Marco 9 |
| RB-017 | Fatura = compras do ciclo − estornos | Marco 9 |
| RB-018 | Pagamento maior que o saldo da fatura é rejeitado | Marco 9 |
| RB-019 | Compra até o fechamento, inclusive, entra na fatura que fecha; fatura movível | Marco 9 |
| RB-020 | Limite disponível = limite − dívida; ultrapassar só avisa | Marco 9 |
| RB-021 | Dias 29 a 31 viram o último dia do mês | Marco 9 |
| RB-022 | DRE por competência; transferências fora | Marco 10 |
| RB-023 (M10) | Fluxo realizado por caixa; compra no cartão só no pagamento | Marco 10 |
| RB-024 (M10) | Previsto pelo valor bruto no vencimento | Marco 10 |
| RB-025 (M10) | Atrasado vira pendente no mês atual da projeção | Marco 10 |
| RB-026 (M10) | Saldo inicial + entradas − saídas = saldo final; fórmula do saldo da conta | Marco 10 |
| RB-027 (M10) | Projeção não inclui compras futuras não lançadas | Marco 10 |
| RB-028 (M10) | Categoria sem grupo cai em "Sem grupo" | Marco 10 |
| RB-029 (M10) | Lançamento no sentido oposto abate o grupo | Marco 10 |
| RB-023 (M11) | Receber empréstimo e amortizar principal não são receita nem despesa | Marco 11 |
| RB-024 (M11) | Encargos são despesa financeira | Marco 11 |
| RB-025 (M11) | Parcela paga não é editada, só desfeita | Marco 11 |
| RB-026 (M11) | Saldo devedor nunca negativo | Marco 11 |
| RB-027 (M11) | Recálculo só altera parcelas em aberto | Marco 11 |
| RB-028 (M12) | Patrimônio líquido = caixa + bens − cartões − dívidas | Marco 12 |
| RB-029 (M12) | Transferências e pagamentos não mudam o patrimônio por si só | Marco 12 |
| RB-030 | Bem vale zero antes da primeira avaliação | Marco 12 |
| RB-031 | Balanço de uma data usa só movimentos até ela | Marco 12 |
| RB-032 | Patrimônio usa valor de mercado; saldo da conta `investment` fica fora | Marco 13 |
| RB-033 | Compra e aporte são transferências | Marco 13 |
| RB-034 | Ganho na venda = produto − custo médio × quantidade | Marco 13 |
| RB-035 | Provento é receita financeira; não reduz o custo | Marco 13 |
| RB-036 | Custo médio ponderado móvel, com taxas | Marco 13 |
| RB-037 | Valorização não realizada não entra no DRE | Marco 13 |
| RB-038 | Ganho de renda variável fora da base anual | Marco 14 |
| RB-039 | Vendas de ações até R$ 20 mil no mês: isento no mês | Marco 14 |
| RB-040 | Prejuízo compensa só a mesma modalidade, acumulando | Marco 14 |
| RB-041 | Bens e direitos pelo custo | Marco 14 |
| RB-042 | Parâmetros fiscais versionados por ano | Marco 14 |
| RB-043 | Nenhum CPF/CNPJ de terceiro armazenado | Marco 14 |
| RB-044 | Prêmio é despesa do período | Marco 15 |
| RB-045 | Simulação em valores reais | Marco 15 |
| RB-046 | Patrimônio-alvo = (renda − benefício) × 12 ÷ taxa de retirada | Marco 15 |
| RB-047 | Progresso usa só investimentos, salvo escolha | Marco 15 |
| RB-048 | Retirada e retorno são premissas do usuário | Marco 15 |

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
| R-009 | Retenção do backup não confirmada (fechado: 7 dias) | discovery 15 |
| R-11.1 | `ALTER TYPE ... ADD VALUE` em migração | Marco 11 |
| R-11.3 | "Conta de caixa" precisa excluir `loan` (e depois `investment`): um único predicado, `NON_CASH_TYPES` | Marco 11 |
| R-12.1 | Avaliação de bem desatualizada distorce o patrimônio (mostrar a data da última avaliação) | Marco 12 |
| R-12.3 | Saldo inicial é "de hoje para trás": meses anteriores ao uso mostram só o saldo inicial | Marco 12 |
| R-13.5 | Cotação desatualizada passa despercebida (mostrar a data e avisar após 3 dias úteis) | Marco 13 |
| R-15.3 | Prêmio duplicado entre recorrência e conta a pagar (a apólice é a única origem) | Marco 15 |
| R-15.5 | Dado sensível de seguro: só metadados, sem número de apólice nem documentos | Marco 15 |
