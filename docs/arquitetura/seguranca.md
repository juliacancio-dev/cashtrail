# Segurança

Threat model **proporcional** ao CashTrail: aplicação pessoal com cadastro aberto na demonstração, código-fonte público (nada de segurança por obscuridade) e dados sensíveis limitados a finanças pessoais. Não há cartão real processado nem dados de terceiros.

Para relatar uma vulnerabilidade, veja [SECURITY.md](../../SECURITY.md).

## Ameaças e controles

| Ativo | Ameaça | Controle | Onde |
|---|---|---|---|
| Credenciais | Força bruta, *credential stuffing* | Rate limiting de 5/min por IP em login, pedido de recuperação e redefinição de senha (SEC-006); 10/min na importação | `auth/router.py`, `statement_import/router.py` |
| Senhas | Vazamento do banco | Hash Argon2; resposta de login não diz qual campo errou | `core/security.py` |
| Tokens | Roubo via XSS | Access token só em memória; refresh em cookie `httpOnly`, `Secure`, `SameSite=Strict` ([ADR-006](../decisoes/ADR-006-jwt-httponly-cookie.md)) | `lib/api-client.ts`, `auth/router.py` |
| Sessão | Token antigo após troca de senha | Tokens emitidos antes de `password_changed_at` são rejeitados | `core/dependencies.py` |
| Cookie de refresh | CSRF | `SameSite=Strict` + header `X-Requested-With` obrigatório nas rotas que dependem só do cookie | `core/dependencies.py` |
| Dados entre usuários | Acesso cruzado por bug de autorização | `CurrentUser` em toda rota protegida; toda consulta filtra por `user_id` (RNF-001, SEC-002); teste `test_user_cannot_access_another_users_*` em cada slice | todas as slices |
| Banco | SQL injection | Só SQLAlchemy ORM com parâmetros; nada de SQL montado por concatenação | — |
| Entrada | Dados malformados | Validação Pydantic em toda rota (SEC-003) | `schemas.py` |
| Upload de extrato | Arquivo gigante ou malformado | Só CSV, até 2 MB e 5.000 linhas, parsing isolado com erro por linha (SEC-004) | `statement_import/parser.py` |
| CSV exportado | Injeção de fórmula ao abrir no Excel | Células de texto iniciadas por `= + - @`, tab ou CR ganham `'` na frente; coberto por teste | `reports/csv_export.py` |
| Recuperação de senha | Enumeração de e-mails; token reaproveitado | Resposta igual exista ou não a conta; só o hash do token é guardado; uso único e expiração de 30 min | `auth/` |
| Segredos | Vazamento no repositório público | Variáveis de ambiente e *secrets* do Container App (`secretref`); `.env` no `.gitignore`; token da brapi nunca vai a log, erro ou frontend (testado) (SEC-005) | `core/config.py`, `deploy.yml` |
| Origem | Outro site chamando a API com credenciais | CORS restrito ao domínio do frontend (`CORS_ALLOWED_ORIGINS`) | `main.py` |
| Nuvem | Credencial de deploy vazada | Login no Azure por OIDC com credenciais federadas, sem segredo de longa duração no GitHub | `deploy.yml`, `db-lifecycle.yml` |
| Dados | Perda por falha de infraestrutura | Backup automático do PostgreSQL Flexible Server, retenção de 7 dias (conferido em 2026-10-15) | Azure |

## Lacunas conhecidas

| Item | Situação | Próximo passo |
|---|---|---|
| Key Vault | O recurso existe, mas os segredos são colados como *secrets* do Container App, sem referência viva ao Key Vault | Backlog: Key Vault com referência viva |
| Dependências | Não há `.github/dependabot.yml` no repositório | Configurar Dependabot para pip, npm e GitHub Actions |
| Banco com acesso público | O PostgreSQL aceita conexões públicas (simplicidade do MVP), protegido por senha forte | Avaliar rede privada se o projeto crescer |
| Rate limit por instância | O limite vale por réplica; correto enquanto houver uma só ([ADR-018](../decisoes/ADR-018-migracoes-na-subida.md)) | Mover o contador para um armazenamento compartilhado se escalar |
| Monitoramento | Sem alertas de produção | Backlog |

## Fora do escopo

| Item | Por quê |
|---|---|
| WAF dedicado | Desproporcional para tráfego pessoal; validação de entrada cobre a superfície realista |
| MFA | Melhoria possível, não exigida pelo risco atual |
| Log de auditoria completo | O registro de importações cobre o caso mais relevante |
| Obrigações da LGPD | A autora é titular e controladora dos próprios dados; revisitar se outras pessoas passarem a usar o app com dados reais |

## Ao mudar código

- Rota nova que acessa dados do usuário: use `CurrentUser`, filtre por `user_id` e escreva o teste de isolamento.
- Configuração nova com segredo: entra em `core/config.py` com padrão seguro para desenvolvimento e vai para produção como *secret*, nunca em texto puro no workflow.
- Exportação nova de CSV: passe pela proteção de `csv_export.py`.
- Integração externa nova: token só no backend, falha isolada (não derruba a API) e nenhum teste chamando a rede.
