# CashTrail — Pesquisa de APIs e Integrações / Serviços de Nuvem (FASE 5)

> Fontes consultadas em 2026-09-15. Este documento resolve a pendência do RNF-006/`00-project-brief.md` sobre limites do Azure for Students, na medida do que existe documentação oficial — valores promocionais podem mudar, então revalidar antes do deploy real.

## Azure for Students — validação da premissa de orçamento

- **FATO (fonte oficial Microsoft)**: US$100 de crédito, sem necessidade de cartão de crédito, válido por 12 meses, mais um conjunto de "sempre grátis" (~25+ serviços). Renovável anualmente enquanto for estudante (verificação por e-mail acadêmico ou GitHub Student Developer Pack).
- **Risco identificado (relato de usuários no fórum oficial da Microsoft, não fato garantido)**: há relatos de renovação não creditando o valor esperado — vale conferir o saldo real assim que a conta for criada/renovada, não assumir que os US$100 estarão sempre disponíveis automaticamente.
- Fonte: [azure.microsoft.com/free/students](https://azure.microsoft.com/en-us/free/students)

## Banco de dados — Azure Database for PostgreSQL Flexible Server

- **Finalidade**: banco relacional gerenciado, compatível com PostgreSQL + SQLAlchemy/Alembic (stack já definida).
- **FATO**: não existe um "free tier" permanente documentado para este serviço — o modelo é pay-as-you-use. Camada mais barata (Burstable B1ms) custa a partir de ~US$12/mês só de compute; armazenamento, backup e alta disponibilidade são cobrados à parte.
- **Vantagem de custo relevante**: o servidor pode ser parado sob demanda (billing de compute para imediatamente); útil para não gastar crédito quando o projeto não está em uso ativo (ex: parar fora de horário de desenvolvimento).
- **Cobrança**: por hora completa provisionada, mesmo que o servidor exista só por poucos minutos naquela hora.
- **Implicação de custo**: este serviço vai consumir o crédito de US$100 do Azure for Students, não ficará em "sempre grátis". Precisa entrar explicitamente na FASE 6 (custos) como item de consumo do crédito, não como grátis.
- Fonte: [Azure Database for PostgreSQL Flexible Server — Pricing](https://azure.microsoft.com/en-us/pricing/details/postgresql/flexible-server/), [Compute Options — Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/compute-storage/concepts-compute)

## Backend — hospedagem do FastAPI: Azure Container Apps vs. App Service

**DECISÃO (preliminar, a confirmar na FASE 7 — Stack):**

**ALTERNATIVAS:**
1. **Azure Container Apps**: deploy de imagem Docker, modelo serverless com *scale-to-zero*.
2. **Azure App Service**: PaaS tradicional, tem tier "Free" mas só para dev/teste (sem "Always On", inadequado pra uma API real).

**EVIDÊNCIAS:**
- Container Apps inclui gratuitamente, por assinatura/mês: 2 milhões de requisições, 180.000 vCPU-segundos e 360.000 GiB-segundos — cobrança por segundo depois disso.
- Container Apps suporta *scale to zero* (custo zero quando ninguém está usando) — encaixa bem com um app de uso pessoal/intermitente (você, sozinha, não é tráfego constante).
- App Service exige "Always On" pra manter a API responsiva sem cold start, o que implica instância sempre ligada (= sempre cobrando), mesmo ociosa.

**TRADE-OFFS:** Container Apps é mais barato para tráfego intermitente (seu caso real), mas introduz *cold start* após período ocioso — primeira requisição depois de inatividade pode ser mais lenta. App Service evita cold start, mas custa mais por ficar sempre ligado.

**RECOMENDAÇÃO:** Azure Container Apps.

**POR QUÊ:** o padrão de uso real (uma usuária, uso não contínuo) se encaixa exatamente no caso ideal de *scale-to-zero*; o cold start ocasional é um trade-off aceitável para um projeto de portfólio/uso pessoal, e o free tier mensal provavelmente cobre o uso real sem consumir o crédito de US$100.

**CONFIANÇA:** Média — depende de validar, na prática, se o cold start é aceitável para a experiência de uso (candidato a checar depois do deploy da primeira slice, não é um risco que bloqueia a decisão agora).

Fonte: [Azure Container Apps — Pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/), [App Service vs Container Apps — Microsoft Learn Q&A](https://learn.microsoft.com/en-nz/answers/questions/1337789/azure-app-service-vs-azure-container-apps-which-to)

## Frontend — hospedagem do Next.js

- **Azure Static Web Apps (tier Free)**: 100 GB de banda/mês grátis, SSL e domínio customizado grátis, 1 milhão de execuções grátis de Azure Functions (se precisar de API própria no front). Integração nativa com GitHub Actions para deploy automático.
- **⚠️ RISCO IDENTIFICADO — precisa de SPIKE antes de comprometer a arquitetura**: o suporte a Next.js **híbrido** (SSR/rotas dinâmicas) no Static Web Apps está em **Preview**, segundo a documentação oficial da Microsoft. Isso significa que pode ter limitações não documentadas ou mudar antes de virar GA (general availability).
- **Alternativa já considerada no plano original**: Vercel (mantenedora do Next.js) — suporte de primeira classe, tier gratuito generoso, mas sai do ecossistema Azure.
- **RECOMENDAÇÃO PRELIMINAR**: fazer um SPIKE curto (deploy de um Next.js mínimo com uma rota dinâmica simples) no Static Web Apps antes de comprometer a arquitetura de produção a ele. Se o Preview se mostrar instável/limitado, usar Vercel para o frontend e manter só o backend na Azure — isso não compromete o objetivo de "mostrar competência em Azure", já que a parte mais demonstrável (API, banco, CI/CD) continua lá.
- Fonte: [Azure Static Web Apps — Pricing](https://azure.microsoft.com/en-us/pricing/details/app-service/static/), [Next.js hybrid on Static Web Apps (Preview) — Microsoft Learn](https://learn.microsoft.com/en-us/azure/static-web-apps/nextjs)

## Storage — arquivos de extrato importados (CSV/OFX)

- **Azure Blob Storage**: sem free tier permanente documentado na página oficial de preços; historicamente a oferta de conta gratuita inclui algo como 5 GB de LRS por 12 meses, mas isso é uma oferta promocional, não uma garantia contínua.
- **Custo real fora de qualquer free tier**: ~US$0,018/GB/mês (tier Hot). Para o volume esperado (arquivos de extrato pessoais, poucos MB por importação), o custo é **irrelevante** mesmo pago integralmente — na casa de centavos por mês.
- **Risco real não é custo, é retenção/privacidade**: extratos bancários são dados sensíveis (SEC/LGPD). Tratar isso na FASE 11 (segurança), não aqui.
- Fonte: [Azure Blob Storage — Pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/)

## CI/CD — GitHub Actions

- **FATO (fonte oficial GitHub, 2026)**: para **repositórios públicos**, runners padrão do GitHub (Linux/Windows/macOS) são gratuitos e sem limite prático de minutos. CashTrail será público (é peça de portfólio), então **CI não consome orçamento nenhum**.
- Fonte: [GitHub Actions billing — GitHub Docs](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions)

---

## Resumo para a FASE 6 (Custos)

| Componente | Custo esperado | Fonte de orçamento |
|---|---|---|
| Backend (Azure Container Apps) | Provavelmente dentro do free tier mensal (uso pessoal, baixo tráfego) | Grátis / crédito se ultrapassar |
| Banco (Azure PostgreSQL Flexible Server) | ~US$12+/mês (sem free tier) | Consome crédito de US$100 |
| Frontend (Static Web Apps ou Vercel) | Grátis (tier Free de qualquer um dos dois) | Grátis |
| Storage de extratos (Blob Storage) | Centavos/mês | Grátis (free tier promocional) ou consumo irrisório de crédito |
| CI/CD (GitHub Actions) | Zero (repo público) | Grátis |

**Item de maior risco de orçamento**: o banco de dados é o único componente sem free tier — é ele que vai consumir a maior parte do crédito de US$100/ano. Cálculo detalhado de cenários (baixo/esperado/alto uso) fica para `06-costs.md`.

**SPIKE recomendado antes da FASE 8 (Arquitetura) travar a decisão de frontend**: testar Next.js híbrido no Azure Static Web Apps (Preview) com uma página simples de rota dinâmica, para validar se atende ou se migramos o frontend para Vercel.

---

**STATUS**: Pronto para avançar, com 1 SPIKE recomendado (não bloqueante — pode ser feito em paralelo com a FASE 6).

Seguimos para a **FASE 6 — Análise de Custos** (cenários de baixo/esperado/alto uso, com base nos preços levantados aqui)?
