# Visão do produto

## Problema

Controlar as finanças pessoais exige juntar o que está espalhado: várias contas, cartões com faturas que fecham em datas diferentes, contas fixas, dívidas, investimentos e, uma vez por ano, o imposto de renda. As ferramentas comuns registram gastos, mas não ligam essas peças: o pagamento da fatura aparece como gasto (e a compra também), a dívida não aparece no patrimônio, o investimento vira "despesa".

O CashTrail tem um segundo objetivo, assumido desde o início: ser a peça principal de portfólio da autora, provando com evidência real (testes, CI, deploy em nuvem) a stack Python que ela usa no trabalho, mais um frontend moderno. Por isso CI/CD, testes contra banco real e decisões documentadas pesam mais do que pesariam num projeto só de uso pessoal.

## Proposta

Um **ERP pessoal**: lança uma vez e alimenta tudo. A compra no cartão vira despesa no DRE, entra na fatura, aparece no fluxo de caixa no vencimento e reduz o patrimônio, sem que nada seja contado duas vezes.

"ERP" aqui é integração ponta a ponta da vida financeira pessoal. Não é vendas, estoque, nota fiscal, agenda nem gestão de documentos.

## Para quem

- **Usuária principal:** a autora, que usa o app de verdade, com seus próprios dados.
- **Visitantes:** recrutadores e pessoas desenvolvedoras que avaliam o projeto pela demonstração pública e pelo código. A demonstração aceita cadastro, e cada usuário só vê os próprios dados ([ADR-002](../decisoes/ADR-002-multi-user-from-start.md)).

## O que o sistema faz hoje

| Área | Funcionalidades | Desde |
|---|---|---|
| Acesso | Cadastro, login, sessão por cookie seguro, recuperação de senha por e-mail | Marcos 2 e 7 |
| Cadastros | Contas (com saldo inicial), categorias (com grupo de DRE e marca fiscal), lançamentos | Marcos 2, 3 e 10 |
| Entrada de dados | Importação de extrato CSV com pré-visualização e aviso de duplicatas | Marco 7 |
| Planejamento | Orçamentos por categoria, metas de economia, recorrências | Marcos 4 e 5 |
| Compromissos | Contas a pagar e a receber com baixa parcial e parcelamento; transferências | Marcos 8 e 9 |
| Cartões | Faturas por ciclo, compras parceladas, pagamento como transferência, limite | Marco 9 |
| Dívidas | Empréstimos e financiamentos (Price, SAC), baixa separando principal e juros, amortização extra | Marco 11 |
| Relatórios | DRE por competência, fluxo de caixa previsto × realizado com projeção, exportação CSV | Marco 10 |
| Patrimônio | Bens com avaliações, balanço pessoal, evolução mensal | Marco 12 |
| Investimentos | Carteira, custo médio, proventos, cotações automáticas, comparação com o CDI | Marco 13 |
| Impostos | Apoio ao IRPF: dossiê anual, estimativa completa × simplificada, DARF de renda variável | Marco 14 |
| Longo prazo | Seguros com alerta de renovação; simulador de independência financeira | Marco 15 |
| Interface | Calendário do dinheiro como tela inicial, tema claro e escuro, navegação em cápsula | Marcos 16 e 17 |

O detalhe de cada marco está no [CHANGELOG](../../CHANGELOG.md); o que vem a seguir, no [roadmap](../roadmap.md).

## Princípios

1. **Cada movimentação conta uma vez.** É a regra que separa o CashTrail de um app de gastos. Ver [regras de negócio](regras-de-negocio.md).
2. **O sistema não inventa números.** Previsões dizem o que não sabem; premissas (retorno, taxa de retirada) são editáveis e rotuladas; valores fiscais citam a fonte, e o que não foi verificado aparece como tal.
3. **Regra de negócio só no backend.** O frontend exibe o que a API calcula; conta de dinheiro tem teste de propriedade.
4. **Calmo antes de completo.** A interface mostra um número principal e uma frase; ações e filtros aparecem quando pedidos.

## Fora do escopo

| Item | Por quê |
|---|---|
| Integração bancária automática (Open Finance) | Agregadores custam de R$ 2.500 a R$ 6.000 por mês (pesquisa de 2026-09, [02-market-research](../historico/discovery/02-market-research.md)) |
| Importação OFX | O CSV cobre os bancos testados; OFX fica para quando houver necessidade real |
| Partidas dobradas | Complexidade sem ganho proporcional para uso pessoal ([ADR-009](../decisoes/ADR-009-partida-simples.md)) |
| Gerar ou transmitir a declaração do IRPF | Risco legal e formato proprietário; o produto é apoio ([ADR-016](../decisoes/ADR-016-parametros-fiscais-por-ano.md)) |
| Cálculo do benefício do INSS | Regras de transição extensas e não verificadas; o usuário informa o valor esperado |
| MFA, WAF, log de auditoria completo | Desproporcionais ao risco atual ([segurança](../arquitetura/seguranca.md#fora-do-escopo)) |

## Restrições

- Custo de nuvem dentro do crédito Azure for Students; por isso o banco desliga à noite ([deploy e operação](../guias/deploy-e-operacao.md#agenda-do-banco)).
- Nenhuma sobreposição com o trabalho profissional da autora: nem domínio, nem lógica, nem interface inspirados nele.
- Código público, com todos os direitos reservados ([LICENSE](../../LICENSE)).
