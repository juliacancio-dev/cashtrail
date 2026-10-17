# Roteiros de verificação no navegador (Playwright)

Scripts ad-hoc usados nos Marcos 8 a 15 para provar cada tela num navegador de verdade (não são testes do CI). Cada roteiro cria um usuário novo pela API, monta o cenário, usa a interface e confere os números com o backend.

| Arquivo | Cobre |
|---|---|
| `e2e-m8-commitments.mjs` | contas a pagar/receber (Marco 8) |
| `e2e-cards.mjs` | cartões e faturas (Marco 9) |
| `e2e-m10.mjs` | saldo inicial, DRE e fluxo de caixa (Marco 10) |
| `e2e-m11.mjs` | dívidas, parcelas, amortização (Marco 11) |
| `e2e-m12.mjs`, `chart-m12.mjs` | bens e patrimônio (Marco 12) |
| `e2e-m13.mjs` | investimentos, com brapi e Banco Central **reais** (Marco 13) |
| `e2e-m14.mjs` | imposto de renda (Marco 14) |
| `e2e-m15.mjs` | seguros e independência financeira (Marco 15) |

## Como rodar (PowerShell, na raiz do repositório)

1. Banco local ligado: `docker compose up -d db` (Postgres em `localhost:5544`).
2. Migrações no banco **local** (o `backend/.env` aponta para o Azure, então sempre sobrescreva):
   ```powershell
   cd backend
   $env:DATABASE_URL="postgresql+psycopg://cashtrail:cashtrail@localhost:5544/cashtrail"
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```
3. Backend na porta **8020** (sem `--reload`):
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn src.main:app --port 8020
   ```
4. Build estático do frontend apontando para esse backend, e servidor estático:
   ```powershell
   cd ..\frontend
   $env:NEXT_PUBLIC_API_URL="http://localhost:8020"; npm run build
   python ..\scripts\e2e\static_server.py out 3000
   ```
5. Instalar o Playwright uma vez e rodar um roteiro:
   ```powershell
   cd ..\scripts\e2e
   npm install
   npx playwright install chromium
   node e2e-m15.mjs
   ```

## Observações

- Use sempre `localhost`, nunca `127.0.0.1`: o cookie de refresh é `SameSite=strict` e os dois contam como sites diferentes.
- O login tem limite de 5 por minuto; se vários roteiros seguidos derem `429`, espere um minuto.
- Os `404` de `__next.*.txt` no console são só arquivos de prefetch que o servidor estático de teste não serve.
- `e2e-m13.mjs` chama a brapi e o Banco Central de verdade (PETR4 funciona sem token).
- Os roteiros gravam capturas de tela (`*.png`) na própria pasta; elas não devem ser commitadas.
