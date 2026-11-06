# Política de segurança

## Relatando uma vulnerabilidade

**Não abra uma issue pública** para falhas de segurança.

Use o recurso de [relato privado de vulnerabilidades](https://docs.github.com/pt/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) do GitHub (aba **Security → Report a vulnerability** deste repositório) ou entre em contato com a mantenedora pelo perfil do GitHub. Inclua:

- o que é afetado (rota, tela ou componente);
- os passos para reproduzir;
- o impacto que você observou ou espera.

Você recebe uma resposta assim que possível. Por ser um projeto pessoal, não há prazo garantido nem programa de recompensa.

## Escopo

Vale para o código deste repositório e para a demonstração publicada. Testes contra a demonstração devem usar contas criadas por você, sem tentar acessar dados de outros usuários, sem negação de serviço e sem automação em volume.

## Versões

Só a versão publicada a partir da `main` recebe correções.

## Mais informações

O threat model e os controles estão em [docs/arquitetura/seguranca.md](docs/arquitetura/seguranca.md).
