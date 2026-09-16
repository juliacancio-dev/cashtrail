# CashTrail — Pesquisa de Soluções Existentes (FASE 2)

> Fontes consultadas em 2026-09-15 (ver links ao final de cada seção). Onde não há fonte oficial, isso está marcado explicitamente.

## Open source (referência de arquitetura)

### Firefly III
- **Problema resolvido**: gestão financeira pessoal completa, self-hosted.
- **Funcionalidades**: partida dobrada (cada transação tem origem e destino), multi-moeda, orçamentos/categorias/tags, importador CSV/OFX/QIF com regras de categorização automática, transações recorrentes, relatórios, API REST completa.
- **Modelo de preço**: grátis, AGPLv3, self-hosted (Docker/Kubernetes).
- **Ponto forte**: modelo de dados maduro (partida dobrada), boa referência para `08-data-model.md`.
- **Ponto fraco**: exige conhecimento de contabilidade do usuário final; curva de aprendizado alta.
- **Aprendizado para o CashTrail**: avaliar partida dobrada vs. saldo simples como decisão explícita na FASE 10 — não copiar automaticamente por ser "mais robusto".
- Fonte: [firefly-iii.org](https://firefly-iii.org/), [Review 2026](https://www.expensesorted.com/blog/147_firefly_iii)

### Actual Budget
- **Problema resolvido**: orçamento estilo envelope (open source, MIT), alternativa direta ao YNAB.
- **Funcionalidades**: orçamento zero-based, local-first com criptografia ponta a ponta opcional, offline-first, sync entre dispositivos.
- **Modelo de preço**: grátis; sync bancário via SimpleFIN (~US$1,50/mês) — não cobre bancos brasileiros.
- **Ponto fraco reconhecido pela comunidade**: recursos multi-usuário/família ainda fracos.
- **Aprendizado**: padrão de UX "orçamento por categoria com meta" já validado — usar como referência de fluxo, não de código.
- Fonte: [Actual vs YNAB](https://actualbudget.org/blog/2024-07-01-actual-vs-ynab/), [Review 2026](https://www.expensesorted.com/blog/144_actual_budget)

## SaaS brasileiro (concorrência direta)

### Mobills
- ~10M+ instalações, freemium.
- Grátis: 1 conta/cartão, sync 1x/dia. Premium R$18–19,90/mês: contas ilimitadas, integração bancária automática, investimentos, relatórios avançados.
- Fonte: [techtudo.com.br](https://www.techtudo.com.br/tudo-sobre/mobills/), [mobills.com.br/pricing](https://www.mobills.com.br/pricing/)

### Organizze
- Mais antigo do mercado BR (desde 2011), foco em simplicidade.
- Plano manual R$35/mês; plano "Conectado" (Open Finance) R$45/mês, até 3 conexões bancárias/dia.
- Fonte: [organizze.com.br/planos](https://www.organizze.com.br/planos/)

**Aprendizado conjunto**: mesmo os líderes de mercado cobram caro justamente pela *conexão bancária automática*, não pelo CRUD manual. Sinal forte de que a integração bancária é o componente caro/difícil do domínio.

## Achado crítico — Open Finance Brasil (relevante à decisão sobre integração bancária futura, ver `00-project-brief.md`)

- **FATO (fonte oficial)**: conectar-se diretamente ao Open Finance Brasil exige virar "instituição participante" certificada — dois processos de certificação (segurança FAPI + conformidade funcional), certificado digital ICP-Brasil, registro dinâmico de cliente (DCR) e conformidade regulatória do Banco Central. **Inviável para desenvolvedor individual** — barreira regulatória, não técnica.
  Fonte: [Open Finance Brasil — Guia de Certificação](https://openfinancebrasil.atlassian.net/wiki/spaces/OF/pages/155910145)
- **FATO (relato de mercado, não documentação oficial de preço)**: o caminho realista para um dev independente seria um agregador terceirizado (Pluggy, Belvo) — cotações relatadas por um desenvolvedor: **Pluggy ~R$2.500/mês, Belvo ~R$6.000/mês**. Pluggy oferece trial gratuito de 2 semanas, mas não há tabela pública de preço para baixo volume.
  Fonte: [Pluggy Pricing](https://www.pluggy.ai/pricing), [relato TabNews](https://www.tabnews.com.br/GuilhermeVieira/estou-desenvolvendo-um-app-de-financas-pessoais-e-nao-consigo-pagar-o-open-finance-pluggy-r2-5k-mes-belvo-r6k-mes-tecnospeed-r1-5k-de-entrada-r540)

**Impacto na decisão registrada em `00-project-brief.md`**: a integração bancária real via Open Finance não é algo que acontecerá organicamente como "próxima fase" — é bloqueada por custo/regulação, não só esforço de código. Tratar como item aspiracional/stretch distante no roadmap (`04-roadmap.md`), não como item no caminho crítico. O modelo de dados continua sendo desenhado para não fechar essa porta (custo ~zero agora), mas a expectativa de execução real dessa integração deve ser baixa.

---

**STATUS**: Pronto para avançar para FASE 3 (Requisitos).
