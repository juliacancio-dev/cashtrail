# Integrações externas

Serviços e fontes de fora do CashTrail, com o que foi verificado, quando e o que continua em aberto. Nenhum teste automatizado chama a rede: os provedores são sempre substituídos por versões falsas.

| Serviço | Uso | Autenticação | Falha |
|---|---|---|---|
| [Banco Central — SGS](#banco-central-sgs) | CDI (comparativo da carteira) e IPCA (contexto da independência) | nenhuma | o plano e a carteira continuam; o índice some |
| [brapi.dev](#brapidev) | cotações de ações, FIIs e ETFs | `BRAPI_TOKEN` (opcional) | vale a última cotação |
| [Azure Communication Services](#azure-communication-services-email) | e-mail de recuperação de senha | connection string | sem envio; em desenvolvimento o link vai para o log |
| [Receita Federal](#receita-federal) | tabelas e regras do IRPF | não é integração: dados copiados para `tax/parameters/<ano>.json` | ano sem arquivo = erro explícito |

## Banco Central (SGS)

- **Séries:** CDI diário, série **12**; IPCA mensal, série **433**.
- **Limites:** a consulta exige datas e aceita no máximo 10 anos por janela; o provedor divide pedidos maiores em janelas.
- **Verificado:** chamadas reais em 2026-10-15.
- **Cache:** o IPCA de 12 meses é guardado pelo dia.

## brapi.dev

- **Plano grátis (verificado em 2026-10-15):** 15.000 requisições por mês, 1 ativo por requisição, atraso de 30 minutos, histórico de 3 meses.
- **Sem token:** só os ativos de teste do sandbox (PETR4, VALE3, MGLU3, ITUB4). Que os demais exigem token é inferência, não confirmado.
- **Proteções no CashTrail:** teto mensal `QUOTES_MONTHLY_CAP` (padrão 10.000) controlado pelo `quote_request_log`; atualização só pelo botão e pelo job diário; cotação com menos de 4 horas não é pedida de novo; o token nunca vai ao frontend, a logs ou a mensagens de erro.
- **Termos de uso (lidos em 2026-10-22, versão de 07/06/2025):** licença limitada e revogável dentro do plano; **proibido** revender, redistribuir ou sublicenciar os dados, criar proxy ou espelho público ou exceder os limites; token confidencial; dados sem garantia; sem exigência de atribuição. O uso pessoal é compatível. Usuários da demonstração pública vendo cotações **pode** ser lido como redistribuição; os termos não tratam do caso.
- **Interface:** `QuoteProvider` em `investments/`, para trocar de fonte sem mexer no resto ([ADR-015](../decisoes/ADR-015-fontes-de-cotacao.md)).

## Azure Communication Services (Email)

- **Recursos:** `cashtrail-email` (Email Communication Services, domínio gratuito do Azure) e `cashtrail-comm` (Communication Services), criados em 2026-10-22.
- **Remetente:** endereço `DoNotReply@<id>.azurecomm.net` do domínio gratuito, guardado no secret `EMAIL_SENDER_ADDRESS`.
- **Verificado:** "Esqueci a senha" testado em produção em 2026-10-22.
- **Aposentadoria do serviço:** **2028-09-30** (guia oficial de retirada da Microsoft). Trocar por SMTP antes; o adaptador em `core/email.py` isola a troca ([ADR-017](../decisoes/ADR-017-email-azure-communication-services.md)).

## Receita Federal

Regras verificadas em páginas oficiais (consulta de 2026-10-15): tabela progressiva e deduções do ano-calendário 2026 (seção "a partir do exercício 2027" da página de tabelas), redutor da Lei 15.270/2025, ações a 15% com isenção de R$ 20.000 por mês em vendas, DARF código 6015 com vencimento no último dia útil do mês seguinte, IRRF de 0,005% sobre a venda, saúde sem limite, PGBL até 12% dos rendimentos tributáveis, PGBL × VGBL, tabela regressiva da previdência (35% a 10%) e da renda fixa (22,5% a 15%), LCI/LCA/poupança isentas.

**Premissas não verificadas** (aparecem na tela de IRPF como tal):

- 20% do desconto simplificado (a Receita publica só o limite de R$ 17.640,00).
- Base do redutor: foi assumido o total dos rendimentos tributáveis; o redutor zera em R$ 88.200.
- FII a 20%, compensação de prejuízo por modalidade, DARF mínimo de R$ 10,00 e IRRF de 0,005% aplicado a FIIs.
- PLR: as fontes divergem na faixa isenta (R$ 7.640,80 × R$ 8.214,40); o sistema usa o valor do informe e não calcula.
- VR/VA fornecidos pelo empregador são isentos (Solução de Consulta, via notícia); em dinheiro, no setor privado, são tributáveis. VT: fonte antiga e secundária.
- ETF, BDR, cripto e fundos não são apurados; day trade só é sinalizado.

A cada ano-calendário, siga a [atualização anual do IRPF](../guias/atualizacao-anual-irpf.md).

## Tesouro Direto

Sem cotação automática: a fonte oficial é um CSV de histórico com centenas de MB e sem o valor do dia. Títulos do Tesouro usam valor manual.
