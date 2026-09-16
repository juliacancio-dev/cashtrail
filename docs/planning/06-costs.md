# CashTrail — Análise de Custos (FASE 6)

> Premissas explícitas, cenários separados de valores exatos quando não há volume real conhecido. Preços em USD conforme fonte oficial (`05-integrations.md`); conversão aproximada BRL só como referência mental, não como valor contratual.

## Achado crítico — o crédito de US$100/ano do Azure for Students pode não cobrir 12 meses de banco de dados sempre ligado

**FATO derivado (cálculo simples a partir da FASE 5):** Azure Database for PostgreSQL Flexible Server (Burstable B1ms) custa a partir de ~US$12/mês **só de compute**, sem contar storage/backup. Rodando 24/7 por 12 meses: **US$12 × 12 = US$144/ano** — isso **sozinho já ultrapassa** o crédito de US$100, mesmo sem considerar backend, storage ou qualquer tráfego.

Isso muda a decisão de arquitetura da FASE 5 de "provavelmente cabe no crédito" para "precisa de uma estratégia deliberada para não estourar o crédito".

**DECISÃO:**
Como manter o banco de dados PostgreSQL gerenciado dentro do orçamento do Azure for Students?

**ALTERNATIVAS:**
1. **Azure Database for PostgreSQL Flexible Server, sempre ligado.** Simples, mas estoura o crédito em ~4-5 meses de uso contínuo (considerando só compute).
2. **Mesmo serviço, mas parado manualmente/via automação quando não está em uso** (o serviço permite start/stop sob demanda, cobrando só as horas ligadas). Reduz custo proporcionalmente ao tempo de uso real.
3. **Provedor alternativo com free tier permanente para Postgres** (ex: Supabase, Neon — não pesquisados em profundidade aqui, fora do escopo desta fase, mas citados como alternativa conhecida do mercado). Custo zero, porém sai do ecossistema Azure — enfraquece a narrativa de portfólio "sei implantar em Azure" para essa peça específica.

**EVIDÊNCIAS:** billing é por hora completa provisionada (FASE 5); parar o servidor interrompe a cobrança de compute imediatamente; um projeto de uso pessoal por uma única usuária não precisa do banco ligado 24/7 com a mesma justificativa que um SaaS multiusuário precisaria.

**TRADE-OFFS:**
- Opção 2 (parar quando ocioso) exige automação (ex: rotina agendada de start/stop, ou você ligar manualmentequando for usar) — mais operação, mas mantém 100% a prova de competência em Azure.
- Opção 3 (Supabase/Neon) é mais simples e garante custo zero permanente, mas dilui o argumento de portfólio de "implementei e operei um banco gerenciado na Azure".

**RECOMENDAÇÃO:** Opção 2 — manter Azure Database for PostgreSQL, mas com rotina de start/stop automatizada (ex: Azure Automation ou GitHub Actions agendado) ligando o banco só nas janelas em que você realmente for usar o app, além de manter always-on durante períodos ativos de busca de emprego (quando recrutadores podem acessar o demo).

**POR QUÊ:** preserva o valor de portfólio (você efetivamente operou um banco gerenciado na nuvem, incluindo otimização de custo — isso é, aliás, um ótimo ponto pra contar em entrevista) sem estourar o crédito.

**CONFIANÇA:** Média — depende de quanto tempo por dia você realisticamente vai deixar o app "ligado"; isso não dá pra saber sem uso real. Recomendo tratar isso como algo a calibrar depois que a Fase 1 (MVP) estiver rodando, não como número fixo agora.

**O QUE PRECISA SER VALIDADO:** custo exato de storage + backup do Postgres Flexible Server — não encontrado na pesquisa da FASE 5 com um número confiável; usar a [Calculadora de Preços da Azure](https://azure.microsoft.com/pricing/calculator/) antes do deploy real para confirmar o total antes de comprometer o crédito.

---

## Cenários de custo mensal

| Item | Custo fixo | Custo variável | Cenário baixo uso | Cenário uso esperado | Cenário alto uso |
|---|---|---|---|---|---|
| Backend (Container Apps) | — | Por requisição/vCPU-s acima do free tier | US$0 (dentro do free tier: 2M req, 180k vCPU-s) | US$0 (mesmo motivo — uso de 1 pessoa não chega perto do limite) | US$0-poucos dólares (mesmo com pico de visitas de recrutadores, improvável ultrapassar 2M req/mês) |
| Banco (PostgreSQL Flexible Server) | ~US$12/mês se sempre ligado | Storage/backup — **não encontrado, validar na calculadora** | ~US$3-4/mês (ligado só ~6h/dia via start/stop) | ~US$6-8/mês (ligado ~12h/dia) | ~US$12/mês (sempre ligado) |
| Frontend (Static Web Apps, tier Free) | US$0 | Acima de 100GB banda/mês | US$0 | US$0 | US$0 (improvável um app pessoal de finanças gerar 100GB/mês de banda) |
| Storage extratos (Blob Storage) | US$0 (free tier promocional ~5GB/12 meses) | ~US$0,018/GB acima disso | Centavos | Centavos | Ainda irrisório (poucos MB por importação) |
| CI/CD (GitHub Actions) | US$0 (repo público) | — | US$0 | US$0 | US$0 |
| Domínio | US$0 (subdomínio Azure, decisão já tomada) | — | US$0 | US$0 | US$0 |

**Premissa de todos os cenários**: usuária única (você), sem tráfego de terceiros usando o app de verdade — só visualização eventual do demo por recrutadores. "Alto uso" aqui significa "muita gente olhando o demo durante um processo seletivo ativo", não crescimento real de base de usuários.

## Estimativa anual (com a estratégia de start/stop recomendada)

- **Baixo/esperado uso**: ~US$36-96/ano de banco de dados → **dentro do crédito de US$100**, com folga se você não deixar o banco ligado o tempo todo.
- **Alto uso / sempre ligado**: ~US$144/ano só de compute do banco → **estoura o crédito** em ~4 meses antes do fim do ano, exigindo pagamento do excedente ou a automação de start/stop.

## Custo inicial (setup)

Nenhum custo de setup identificado além do tempo — todos os serviços cobrados são pay-as-you-go, sem taxa de adesão.

---

**STATUS**: Pronto para avançar, com uma ação recomendada e não bloqueante: implementar a automação de start/stop do banco como parte da FASE 4 do roadmap original (Hardening/Deploy), não precisa ser resolvida agora.

**PENDÊNCIA real**: validar storage/backup do Postgres na calculadora oficial antes do primeiro deploy em nuvem (não antes disso — não trava discovery nem arquitetura).

Seguimos para a **FASE 7 — Definição da Stack** (agora com todos os dados de custo e integração já levantados para justificar cada escolha)?
