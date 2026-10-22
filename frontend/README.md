# CashTrail — Frontend

Interface web do CashTrail, construída com **Next.js (App Router)**, **React**, **shadcn/ui** e **Tailwind CSS**, e publicada como **site estático** servido por nginx.

Visão geral do produto, ADRs e infraestrutura estão no [README principal](../README.md). Este guia cobre o que é específico do frontend: organização do código, comunicação com a API, autenticação, execução e build.

---

## Stack

| Responsabilidade | Biblioteca |
|---|---|
| Framework | Next.js 16 (App Router, `output: "export"`) + React 19 |
| Linguagem | TypeScript |
| Componentes | shadcn/ui (estilo `base-nova`, sobre Base UI) + ícones lucide-react |
| Estilo | Tailwind CSS 4 |
| Formulários e validação | react-hook-form + zod |
| Gráficos | Recharts |
| Servidor em produção | nginx (imagem `nginx:alpine`) |

Requer **Node.js 22**.

## Por que static export

O frontend é exportado como HTML, CSS e JavaScript estáticos (`next build` gera a pasta `out/`). Toda a lógica roda no navegador e conversa com a API pelo `api-client`; não existe servidor Node em produção.

Isso permite servir o site com nginx num Azure Container App, o mesmo tipo de recurso do backend. A alternativa natural, Azure Static Web Apps, foi descartada por bloqueio de política de região na assinatura usada.

A consequência prática é que **não há recursos de servidor do Next.js**: nada de Server Actions, rotas de API, middleware ou rotas dinâmicas sem `generateStaticParams`. Todas as páginas são componentes de cliente (`"use client"`).

## Estrutura

```text
frontend/src/
├── app/                  # uma pasta por rota (page.tsx)
│   ├── layout.tsx        # layout raiz e AuthProvider
│   └── page.tsx          # redireciona para /accounts ou /login
├── features/             # uma pasta por funcionalidade, espelhando as slices do backend
│   └── <nome>/
│       ├── api.ts        # chamadas à API da funcionalidade
│       ├── schemas.ts    # tipos e schemas zod dos formulários
│       └── *.tsx         # formulários, listas e painéis
├── components/
│   ├── app-nav.tsx       # navegação principal
│   └── ui/               # componentes shadcn/ui
└── lib/
    ├── api-client.ts     # fetch autenticado, refresh automático e header CSRF
    ├── api-errors.ts     # tradução de respostas de erro em mensagens
    ├── format.ts         # moeda (BRL), datas e meses
    └── utils.ts          # helper cn() do shadcn
```

A divisão em `features/` segue a mesma ideia dos vertical slices do backend: a página em `app/` monta a tela, e o código de cada funcionalidade fica junto na sua pasta.

### Rotas

| Grupo | Rotas |
|---|---|
| Acesso | `/login`, `/register`, `/forgot-password`, `/reset-password` |
| Visão geral | `/dashboard`, `/net-worth` |
| Cadastros | `/accounts`, `/categories`, `/transactions`, `/import` |
| Planejamento | `/budgets`, `/goals`, `/recurring`, `/commitments`, `/transfers`, `/cash-flow` |
| Crédito e dívidas | `/cards`, `/debts` |
| Patrimônio | `/assets`, `/investments`, `/insurance`, `/retirement` |
| Relatórios e impostos | `/dre`, `/tax` |

## Comunicação com a API

Toda chamada passa por `src/lib/api-client.ts`, que:

- envia o access token no header `Authorization: Bearer`;
- envia o header `X-Requested-With: CashTrail`, exigido pelo backend como defesa contra CSRF;
- usa `credentials: "include"` para que o cookie de refresh trafegue;
- ao receber `401`, tenta renovar o access token uma vez e repete a requisição;
- define `Content-Type: application/json` automaticamente, exceto em uploads (`FormData`).

Os módulos `features/<nome>/api.ts` expõem funções tipadas sobre o `apiClient`. Erros de regra de negócio do backend chegam em `detail` e são convertidos em mensagens por `apiFail` (`src/lib/api-errors.ts`), incluindo o aviso de limite de tentativas (`429`).

## Autenticação

Segue a [ADR-006](../docs/planning/decisions/ADR-006-jwt-httponly-cookie.md):

- O **access token fica apenas em memória**, numa variável do `api-client`. Nunca vai para `localStorage`, `sessionStorage` ou cookies legíveis por JavaScript.
- O **refresh token** fica num cookie `httpOnly` definido pelo backend, inacessível ao JavaScript.
- Ao carregar qualquer página, o `AuthProvider` (`features/auth/auth-context.tsx`) tenta renovar a sessão silenciosamente a partir do cookie e carrega o usuário em `/auth/me`.
- As páginas protegidas usam `useAuth()` e redirecionam para `/login` quando não há usuário.

Recarregar a página perde o access token, mas não a sessão: o refresh silencioso emite um novo.

## Configuração

| Variável | Padrão | Descrição |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8001` | URL base da API |

```bash
cp .env.local.example .env.local
```

Por ser um site estático, a variável é **embutida no JavaScript durante o build**. Mudar o endereço da API exige gerar um novo build (ou uma nova imagem); não adianta alterá-la no container em execução. Por isso ela não deve conter nenhum segredo.

## Executando

Com a API rodando (veja o [README do backend](../backend/README.md#executando)):

```bash
npm install
npm run dev
```

Acesse `http://localhost:3000`. A origem precisa estar em `CORS_ALLOWED_ORIGINS` no backend (o padrão já inclui `http://localhost:3000`).

| Script | O que faz |
|---|---|
| `npm run dev` | Servidor de desenvolvimento com recarga automática |
| `npm run build` | Gera o site estático em `out/` |
| `npm run lint` | ESLint com a configuração do Next.js |

O CI executa `npm run lint` e `npm run build` a cada push e pull request; um build quebrado bloqueia o deploy.

## Build e Docker

O `Dockerfile` usa duas etapas:

1. **build** (`node:22-alpine`): instala as dependências com `npm ci` e roda `npm run build`, recebendo `NEXT_PUBLIC_API_URL` como build arg;
2. **runtime** (`nginx:alpine`): copia `out/` e o `nginx.conf`, que resolve `/rota` para `rota.html` e usa `404.html` como página de erro.

```bash
docker build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8001 -t cashtrail-frontend .
docker run --rm -p 3000:80 cashtrail-frontend
```

Em produção, o workflow [`deploy.yml`](../.github/workflows/deploy.yml) constrói a imagem com a URL pública do backend.

## Verificação no navegador

Não há testes automatizados de interface no CI. Cada tela dos Marcos 8 a 15 foi verificada com roteiros Playwright que criam um usuário, montam o cenário pela API, usam a interface e conferem os números com o backend. Instruções em [`scripts/e2e/`](../scripts/e2e/README.md).

## Adicionando uma tela

1. Crie `src/features/<nome>/` com `schemas.ts` (tipos e schema zod) e `api.ts` (funções sobre o `apiClient`).
2. Crie os componentes da funcionalidade na mesma pasta.
3. Crie `src/app/<rota>/page.tsx` como componente de cliente, protegendo-a com `useAuth()`.
4. Adicione o link em `src/components/app-nav.tsx`.
5. Use `formatCurrency` e `formatDate` de `src/lib/format.ts` para valores e datas; datas `YYYY-MM-DD` são formatadas sem passar por `Date`, para evitar deslocamento de fuso.

## Referências

- [Pesquisa de UI](../docs/planning/21-ui-research.md)
- [ADR-006: tokens e cookies](../docs/planning/decisions/ADR-006-jwt-httponly-cookie.md)
- [Segurança](../docs/planning/11-security.md)
