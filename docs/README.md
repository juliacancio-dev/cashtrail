# Documentação do CashTrail

Esta pasta reúne a documentação do CashTrail que fica fora do código. Ela é versionada no mesmo repositório (*docs as code*), revisada nos mesmos pull requests e segue a divisão do framework [Diátaxis](https://diataxis.fr/): **guias** para tarefas, **referência** para consulta, **explicação** para entender o sistema e **decisões** para saber por que ele é assim.

O que vale para uma única parte do código fica junto dela: [backend](../backend/README.md), [frontend](../frontend/README.md) e [roteiros de navegador](../scripts/e2e/README.md).

## Por onde começar

| Quero... | Leia |
|---|---|
| Entender o produto em 5 minutos | [Visão do produto](produto/visao-geral.md) |
| Entender como o sistema é montado | [Arquitetura](arquitetura/visao-geral.md) |
| Rodar o projeto na minha máquina | [Ambiente local](guias/ambiente-local.md), depois os READMEs de [backend](../backend/README.md#executando) e [frontend](../frontend/README.md#executando) |
| Saber por que uma tecnologia ou regra foi escolhida | [Decisões (ADRs)](decisoes/README.md) |
| Mexer em valores (saldo, DRE, fluxo, patrimônio) | [Regras de negócio](produto/regras-de-negocio.md) |
| Achar um `RF-xxx` ou `RB-xxx` citado no código | [Catálogo de requisitos](referencia/requisitos.md) |
| Publicar uma versão nova | [Deploy e operação](guias/deploy-e-operacao.md) |
| Ver o que já foi feito e o que vem a seguir | [Roadmap](roadmap.md) e [CHANGELOG](../CHANGELOG.md) |
| Propor uma funcionalidade nova | [Como trabalhamos](processo/como-trabalhamos.md) |

## Mapa

```text
docs/
├── README.md                    # este índice
├── roadmap.md                   # estado dos marcos, próximos passos e backlog
│
├── produto/                     # EXPLICAÇÃO: o quê e por quê
│   ├── visao-geral.md           # problema, público, escopo e limites
│   ├── regras-de-negocio.md     # as regras de dinheiro que não podem ser quebradas
│   └── glossario.md             # termos financeiros e do domínio
│
├── arquitetura/                 # EXPLICAÇÃO: como o sistema é montado
│   ├── visao-geral.md           # contexto, containers, vertical slices e dependências
│   ├── modelo-de-dados.md       # tabelas por slice, convenções e migrações
│   └── seguranca.md             # threat model e controles
│
├── decisoes/                    # ADRs no formato MADR, numerados e imutáveis
│
├── referencia/                  # REFERÊNCIA: consulta rápida
│   ├── requisitos.md            # catálogo RF / RB / RNF / SEC citados no código
│   └── integracoes-externas.md  # Banco Central, brapi, ACS e Receita Federal
│
├── guias/                       # GUIAS: passo a passo de uma tarefa
│   ├── ambiente-local.md        # subir tudo localmente e as armadilhas conhecidas
│   ├── deploy-e-operacao.md     # deploy, fumaça, reversão e infraestrutura Azure
│   └── atualizacao-anual-irpf.md
│
├── processo/
│   └── como-trabalhamos.md      # ciclo de um marco, formato de decisão, DoR/DoD
│
├── marcos/                      # documentos de desenho de cada marco (registro)
└── exemplos/                    # arquivos de amostra (extrato CSV)
```

## Convenções

- **Idioma:** português do Brasil; identificadores de código entre crases e em inglês, como no código.
- **Nomes de arquivo:** `kebab-case`, sem acento. Cada pasta tem um `README.md` quando precisa de índice.
- **Uma fonte de verdade por assunto.** Se um fato já está num documento, os outros apontam para ele em vez de repetir. Variáveis de ambiente, por exemplo, ficam só nos READMEs de backend e frontend.
- **Documentação viva × registro.** `produto/`, `arquitetura/`, `referencia/`, `guias/` e `roadmap.md` descrevem o sistema **como ele é hoje** e mudam no mesmo pull request que muda o código. `decisoes/` e `marcos/` são **registros**: não se reescreve o passado, cria-se um documento novo que substitui o antigo.
- **Fatos externos têm fonte e data.** Preços, limites de API e regras fiscais citam a fonte oficial e a data da consulta; o que não foi verificado aparece como tal.
- **Diagramas** em [Mermaid](https://mermaid.js.org/), que o GitHub desenha direto no Markdown.

## Mantendo a documentação

| Mudou... | Atualize |
|---|---|
| Uma regra de cálculo de dinheiro | [regras-de-negocio.md](produto/regras-de-negocio.md) e, se houver ID novo, [requisitos.md](referencia/requisitos.md) |
| Uma tabela ou coluna | [modelo-de-dados.md](arquitetura/modelo-de-dados.md) |
| Uma slice nova ou uma dependência entre slices | [arquitetura/visao-geral.md](arquitetura/visao-geral.md) e o README do [backend](../backend/README.md) |
| Uma escolha difícil de desfazer | um ADR novo em [decisoes/](decisoes/README.md) |
| Um workflow, secret ou recurso de nuvem | [deploy-e-operacao.md](guias/deploy-e-operacao.md) |
| Um marco terminou | [roadmap.md](roadmap.md), [CHANGELOG](../CHANGELOG.md) e o STATUS do documento do marco |
