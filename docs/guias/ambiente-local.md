# Ambiente local

Como subir o CashTrail inteiro na sua máquina e as armadilhas que já custaram tempo. Os comandos de cada parte estão nos READMEs de [backend](../../backend/README.md#executando) e [frontend](../../frontend/README.md#executando); este guia junta tudo e cobre o que é transversal.

## Pré-requisitos

| Ferramenta | Versão | Para quê |
|---|---|---|
| Docker Desktop | atual, **aberto** | banco local e Testcontainers nos testes |
| Python | 3.12+ | backend e testes |
| Node.js | 22 | frontend e roteiros Playwright |

## Caminho rápido (Docker Compose)

Na raiz do repositório:

```bash
docker compose up -d                 # PostgreSQL em localhost:5544 e API em localhost:8001

cd frontend
cp .env.local.example .env.local     # NEXT_PUBLIC_API_URL=http://localhost:8001
npm install
npm run dev                          # http://localhost:3000
```

As migrações rodam na subida da API. Crie uma conta em `http://localhost:3000/register`.

## Caminho completo (como nos roteiros de navegador)

Útil para depurar o backend ou rodar os roteiros de [`scripts/e2e/`](../../scripts/e2e/README.md). Exemplo em PowerShell:

```powershell
# 1. Banco local
docker compose up -d db

# 2. Backend fora do Docker, apontando para o banco LOCAL
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements-dev.txt
$env:DATABASE_URL="postgresql+psycopg://cashtrail:cashtrail@localhost:5544/cashtrail"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8020

# 3. Frontend como build estático apontando para esse backend (outro terminal)
cd frontend
$env:NEXT_PUBLIC_API_URL="http://localhost:8020"; npm run build
python ..\scripts\e2e\static_server.py out 3000
```

No bash, troque `$env:VAR="valor"; comando` por `VAR=valor comando` e `.\.venv\Scripts\` por `.venv/bin/`.

## Testes

| O quê | Comando | Observação |
|---|---|---|
| Backend | `cd backend && pytest -q` | 3 a 4 minutos; Docker aberto; **não** defina `DATABASE_URL` (os testes sobem o próprio PostgreSQL) |
| Frontend | `cd frontend && npm run lint && npx tsc --noEmit && npm run build` | o mesmo que o CI roda |
| Navegador | `node scripts/e2e/<roteiro>.mjs` | precisa do caminho completo acima; ver o [README dos roteiros](../../scripts/e2e/README.md) |

Padrões usados nos testes do backend: data fixa nos testes de relatório (`TODAY = date(2026, 8, 20)`), testes de propriedade para somas e saldos, `begin_nested()` para testar `IntegrityError`, provedores externos sempre falsos, rate limit e agendador desligados.

## Armadilhas conhecidas

| Sintoma | Causa | Solução |
|---|---|---|
| Migração ou dado indo para o banco errado | `backend/.env` pode apontar para um banco remoto | Sempre sobrescreva `DATABASE_URL` para o banco local antes de migrar ou subir a API |
| Login funciona, mas a sessão some ao recarregar | Frontend em `127.0.0.1` e API em `localhost` (ou o contrário): o cookie `SameSite=Strict` trata como sites diferentes | Use **sempre** `localhost` nos dois |
| Porta ocupada ao subir | Serviços locais do Windows (PostgreSQL nativo em 5432/5433, porta 8000 reservada) ou containers de outros projetos | Por isso o Compose usa 5544 e 8001; confira com `netstat -ano` antes de escolher outra |
| A porta continua ocupada depois de parar a API | `uvicorn --reload` deixa processos órfãos no Windows | Rode sem `--reload` |
| A API responde, mas não é a rota que você espera | Outra aplicação local respondendo na mesma porta | Confira `/openapi.json`, não só `/health` |
| Mudou a URL da API e o frontend continua chamando a antiga | `NEXT_PUBLIC_API_URL` é embutida no build | Gere o build de novo |
| `argon2` "Memory allocation error" ou `next build` morrendo | Pouca memória livre | Repita o comando |
| `429 Too Many Requests` em sequência de roteiros | Limite de 5 logins por minuto | Espere um minuto entre roteiros |
| `401` em `/auth/refresh` no console ao abrir `/login` | O app tenta recuperar uma sessão que ainda não existe | Esperado |
| `404` de `__next.*.txt` no console | O servidor estático não acha os arquivos de pré-carregamento do Next 16 | Inofensivo; pendência registrada no [doc 33](../marcos/33-marco-17-acabamento.md) |
| `Select` mostrando o valor cru | Componente do Base UI sem a prop `items` | Passe `items` (`{value, label}[]`); `onValueChange` pode receber `null` |
| ESLint reclamando de `setState` em efeito | Regra do React | Carregue com `.then` e flag `cancelled`; use `useWatch` em vez de `watch` e `reloadKey` para recarregar |
