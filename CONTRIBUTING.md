# Contribuindo com o CashTrail

Obrigada pelo interesse em contribuir. Relatos de bug, sugestões e pull requests são bem-vindos.

Antes de começar, leia a seção [Licença das contribuições](#licença-das-contribuições): o CashTrail **não é open source**, e enviar um pull request implica aceitar os termos descritos ali.

---

## Formas de contribuir

| Tipo | Como |
|---|---|
| Bug | Abra uma issue com os passos para reproduzir, o resultado esperado e o obtido |
| Sugestão de funcionalidade | Abra uma issue descrevendo o problema que ela resolve, antes de escrever código |
| Correção ou melhoria | Siga o [fluxo de pull request](#fluxo-de-pull-request) |
| Documentação | Pull requests de documentação seguem o mesmo fluxo e não exigem issue prévia |

**Falhas de segurança não devem ser relatadas em issues públicas.** Entre em contato diretamente com a mantenedora pelo perfil do GitHub, descrevendo o problema e como reproduzi-lo.

## Antes de escrever código

O CashTrail foi construído a partir de um discovery documentado. Mudanças de comportamento precisam ser coerentes com ele:

- [Requisitos e regras de negócio](docs/planning/03-requirements.md)
- [Arquitetura por vertical slices](docs/planning/09-vertical-slices.md)
- [Modelo de dados](docs/planning/10-data-model.md)
- [Segurança](docs/planning/11-security.md)
- [ADRs](docs/planning/decisions/)

Para funcionalidades novas ou mudanças de arquitetura, **abra uma issue e aguarde alinhamento antes de implementar**. Um pull request que contradiga um ADR precisa vir acompanhado de um novo ADR propondo a mudança.

## Ambiente de desenvolvimento

Siga os guias de cada parte:

- [Backend](backend/README.md#executando): Docker Compose, ambiente virtual Python, migrações e testes
- [Frontend](frontend/README.md#executando): Node.js 22, `npm run dev`

## Fluxo de pull request

1. Faça um fork e crie uma branch a partir de `main`, com nome curto e descritivo (`fix/saldo-cartao-fechamento`, `feat/exportacao-ofx`).
2. Implemente a mudança seguindo os [padrões do projeto](#padrões-do-projeto).
3. Rode as verificações localmente:
   ```bash
   cd backend && pytest
   cd frontend && npm run lint && npm run build
   ```
4. Abra o pull request contra `main`, preenchendo a [descrição](#descrição-do-pull-request).
5. O CI precisa passar. A mantenedora revisa e pode pedir ajustes antes do merge.

Pull requests pequenos e focados em um único assunto são revisados mais rápido.

## Padrões do projeto

### Backend

- Código novo entra numa slice em `backend/src/features/<nome>/`, seguindo a [anatomia de uma slice](backend/README.md#anatomia-de-uma-slice).
- Uma slice acessa outra **apenas pelo `service`**. `transactions` é o núcleo: as outras slices dependem dela, nunca o contrário.
- Toda rota protegida usa `CurrentUser`, e toda consulta filtra por `user_id`.
- Mudanças de schema exigem migração Alembic revisada à mão.
- Configuração nova entra em `src/core/config.py`, com valor padrão seguro para desenvolvimento.
- Valores monetários usam `Decimal`, nunca `float`.

### Frontend

- Código da funcionalidade fica em `frontend/src/features/<nome>/`; a página em `src/app/<rota>/page.tsx` só monta a tela.
- Chamadas à API passam pelo `apiClient` (`src/lib/api-client.ts`).
- O access token nunca é gravado em `localStorage`, `sessionStorage` ou cookie legível.
- O site é exportado como estático: não use Server Actions, rotas de API nem middleware do Next.js.
- Formate moeda e datas com `src/lib/format.ts`.

### Integridade financeira

Toda mudança que afete valores deve preservar a regra de **contagem única**: transferências, pagamento de fatura, compra de investimento e amortização de principal não são receita nem despesa. Se a mudança altera dashboard, DRE, fluxo de caixa ou patrimônio, os testes devem provar que nenhum valor é contado duas vezes.

### Comentários e idioma

- Código, nomes e identificadores em inglês; mensagens ao usuário, comentários e documentação em português.
- Comentários explicam o **porquê** (uma regra de negócio, uma decisão, uma limitação), não o que o código já diz. Quando a regra vem de um requisito ou ADR, cite o identificador (`RB-003`, `ADR-006`).

## Testes

Um pull request está pronto quando atende à [Definition of Done](docs/planning/19-definition-ready-done.md). Em especial:

- **Testes de integração com PostgreSQL real** (Testcontainers) para regras de negócio e rotas novas; não use mocks de banco.
- **Teste de isolamento** para toda rota nova que acesse dados do usuário, no padrão `test_user_cannot_access_another_users_*`.
- **Correções de bug** vêm com um teste que falha antes da correção e passa depois.
- Cálculos (juros, faturas, impostos, posições) ficam em funções puras, com testes unitários cobrindo os casos-limite.

Mudanças de interface devem ser verificadas no navegador. Para telas complexas, considere um roteiro em [`scripts/e2e/`](scripts/e2e/README.md).

## Mensagens de commit

O projeto segue [Conventional Commits](https://www.conventionalcommits.org/pt-br/), com a descrição em português, no imperativo e sem ponto final:

```text
<tipo>(<escopo opcional>): <descrição>
```

| Tipo | Uso |
|---|---|
| `feat` | Funcionalidade nova |
| `fix` | Correção de bug |
| `refactor` | Mudança de código sem alterar comportamento |
| `docs` | Apenas documentação |
| `test` | Apenas testes |
| `ci` | Workflows do GitHub Actions |
| `chore` | Manutenção, dependências e configuração |

Escopos comuns: `backend`, `frontend` ou o nome da slice. Exemplos:

```text
fix(credit_cards): considera o dia de fechamento no ciclo da fatura
feat(frontend): adiciona filtro por conta no fluxo de caixa
```

## Descrição do pull request

Inclua:

- **O quê e por quê:** o problema resolvido e a issue relacionada (`Closes #12`).
- **Como foi testado:** testes adicionados e verificação manual feita.
- **Impacto:** migrações, novas variáveis de ambiente ou mudanças de comportamento visíveis ao usuário.
- **Capturas de tela**, quando a interface mudar.

## Licença das contribuições

O CashTrail é distribuído com **todos os direitos reservados** (veja o arquivo [LICENSE](LICENSE)). Ao enviar um pull request, você declara que:

1. a contribuição é de sua autoria, ou você tem o direito de enviá-la;
2. concede à titular do projeto uma licença perpétua, mundial, gratuita, irrevogável e não exclusiva para usar, modificar, distribuir e sublicenciar a contribuição, inclusive sob outros termos de licença no futuro;
3. não espera remuneração pela contribuição.

Você continua dono do que escreveu e pode usar seu próprio código em outros projetos; a licença acima apenas permite que ele seja incorporado ao CashTrail.
