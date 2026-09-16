# CashTrail — Segurança / Threat Model (FASE 11)

> Threat model proporcional: CashTrail é uma aplicação pessoal, single-tenant lógico com multi-user técnico, código-fonte público no GitHub (sem segurança por obscuridade), dados sensíveis limitados a informação financeira pessoal (não há cartão de crédito real processado, nem dados de terceiros).

## Decisão de arquitetura de segurança: onde guardar o JWT no navegador

**DECISÃO:** Access/refresh token ficam em `localStorage` (mais simples) ou em cookie `httpOnly`?

**ALTERNATIVAS:**
1. **Ambos os tokens em `localStorage`**, enviados via header `Authorization: Bearer`.
2. **Refresh token em cookie `httpOnly` + `Secure` + `SameSite=Strict`**; access token mantido apenas em memória (estado React), nunca persistido.

**EVIDÊNCIAS:** `localStorage` é acessível por qualquer JavaScript rodando na página — se existir uma vulnerabilidade de XSS (mesmo vinda de uma dependência de terceiro, não necessariamente de um bug seu), o token pode ser roubado trivialmente. Cookies `httpOnly` não são acessíveis via JavaScript, o que elimina essa classe específica de ataque.

**TRADE-OFFS:** cookie `httpOnly` exige CORS configurado com `credentials: include` e atenção a CSRF — mitigado com `SameSite=Strict` (o navegador não envia o cookie em requisições disparadas por outro site) e, como defesa em profundidade, checagem de um header customizado (ex: `X-Requested-With`) que só seu próprio frontend adicionaria. `localStorage` é mais simples de implementar, mas deixa o token exposto a qualquer XSS.

**RECOMENDAÇÃO:** refresh token em cookie `httpOnly` + `Secure` + `SameSite=Strict`; access token só em memória (nunca em `localStorage`/`sessionStorage`).

**POR QUÊ:** é o padrão recomendado pela indústria para SPAs com backend próprio (não é um serviço terceiro tipo Auth0 onde outras restrições se aplicam); o custo de setup extra é baixo e elimina a classe de ataque mais comum contra JWT em frontend.

**CONFIANÇA:** Alta.

**O QUE PRECISA SER VALIDADO:** configuração exata de CORS entre o domínio do frontend e do backend na Azure (provavelmente subdomínios diferentes) para o cookie cross-origin funcionar — detalhe de implementação, não bloqueia o discovery.

## Gap descoberto: não há fluxo de recuperação de senha nos requisitos

Revisando `03-requirements.md`, não existe um RF de "esqueci minha senha". Para uso real contínuo (não só demo), isso é uma lacuna genuína — sem esse fluxo, perder a senha significa perder acesso aos próprios dados financeiros.

**Registrando como novo requisito, não decidindo silenciosamente:**
- **RF-013 (novo)**: Recuperação de senha via link enviado por e-mail, com token de uso único e expiração curta.
- **Prioridade sugerida:** Média — não bloqueia a primeira Vertical Slice (auth básico), mas deve entrar antes do MVP ser considerado "pronto para uso real contínuo" (ver `05-mvp.md`, a produzir na próxima fase).
- **Dependência nova:** envio de e-mail transacional. Isso introduz uma integração externa que ainda não pesquisamos (ex: Azure Communication Services Email, SendGrid, Resend). **Recomendo tratar isso como um item pequeno de pesquisa dentro da FASE 12 (MVP)**, não reabrir toda a FASE 5 por causa de um único serviço.

## Threat model (proporcional)

| Ativo/Risco | Ameaça | Controle | Contra qual risco existe |
|---|---|---|---|
| Credenciais de login | Força bruta / credential stuffing | Rate limiting no endpoint de login (SEC-006) | Impede tentativa automatizada de milhares de senhas |
| Token JWT | Roubo via XSS | Refresh em cookie `httpOnly`, access token só em memória (decisão acima) | Elimina exfiltração de token via JavaScript malicioso |
| Dados entre usuários | Vazamento cross-tenant (bug de autorização) | Toda query filtra por `user_id` (RNF-001) + teste automatizado dedicado a isso | Erro de um único endpoint sem essa checagem expõe dados de outro usuário |
| Banco de dados | SQL Injection | Uso exclusivo de SQLAlchemy ORM com queries parametrizadas, nunca SQL string concatenado | ORM previne injeção por padrão quando não se usa `text()` com input não sanitizado |
| Upload de extrato | Arquivo malicioso (tamanho, tipo, encoding malformado) | SEC-004: limite de tamanho, validação de extensão/mimetype, parsing isolado com tratamento de erro | Nega DoS por upload gigante e falha não tratada que derruba o processo |
| Upload de extrato (CSV) | "CSV injection" — célula com fórmula (`=CMD(...)`) executada se o arquivo for aberto depois no Excel | Sanitizar/escapar campos que começam com `=`, `+`, `-`, `@` ao gerar qualquer exportação futura de CSV | Evita que um export do próprio sistema vire vetor de ataque em planilha de terceiro |
| Segredos (DB, JWT secret) | Vazamento no código-fonte (repo é público!) | Azure Key Vault + variáveis de ambiente, nunca hardcoded; `.gitignore` cobrindo arquivos `.env` | Repo público = qualquer segredo commitado por engano é encontrado por scanners automatizados em minutos |
| Comunicação frontend↔backend | Origem não autorizada chamando a API | CORS restrito ao domínio real do frontend | Impede que outro site faça requisições autenticadas em nome do usuário |
| Cookie de refresh token | CSRF (requisição forjada de outro site) | `SameSite=Strict` + checagem de header customizado | Mitiga o principal vetor de CSRF contra cookies |
| Dependências (pip/npm) | Vulnerabilidade conhecida em biblioteca de terceiro | Dependabot habilitado (gratuito em repositório público no GitHub) | Alerta automático quando uma dependência usada tem CVE conhecida |
| Banco de dados (Azure) | Perda de dados (falha de infraestrutura) | Backup automático do Azure Database for PostgreSQL Flexible Server | **Pendente de validação**: política de retenção padrão não foi confirmada na FASE 5/6 — validar antes de considerar o projeto "pronto para uso real" |
| Dados financeiros pessoais | Privacidade/LGPD | Você é ao mesmo tempo titular e controladora dos seus próprios dados — LGPD não impõe obrigações adicionais relevantes nesse cenário específico. **Fica diferente se algum dia outra pessoa usar o sistema com dados próprios** — revisitar então. | Evita over-engineering de compliance que não se aplica ao caso de uso atual |

## O que foi deliberadamente deixado fora (com justificativa)

- **WAF (Web Application Firewall) dedicado**: desproporcional para uma aplicação pessoal de baixo tráfego; Azure Container Apps + boas práticas de validação de entrada já cobrem a superfície de ataque realista.
- **MFA (autenticação de dois fatores)**: seria um bom "nice to have", mas não é um requisito do discovery atual — pode ser adicionado depois como melhoria, não é bloqueante pro MVP nem gera risco desproporcional hoje (dado de uso pessoal, não corporativo).
- **Log de auditoria completo (quem viu o quê, quando)**: decidido na FASE 10 como fora do MVP — `StatementImport` já cobre o caso de auditoria mais relevante (importações).

---

**STATUS**: Pronto para avançar, com um novo requisito registrado (RF-013 — recuperação de senha) que precisa ser incorporado ao MVP na próxima fase.

Seguimos para a **FASE 12 — Definição do MVP**?
