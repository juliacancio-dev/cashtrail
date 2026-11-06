# ADR-002 — Multiusuário desde o início

- **Status:** Aceita
- **Data:** 2026-09-16

## Contexto e problema

No discovery havia uma única usuária real: a própria autora. Um app de uso pessoal poderia dispensar cadastro e login, mas o código é público e o projeto também serve de portfólio.

## Opções consideradas

1. **Usuária única**, sem autenticação real.
2. **Multiusuário completo:** cadastro, login com JWT e `user_id` isolando os dados em toda tabela de domínio.

## Decisão

Escolhida: **multiusuário completo**, porque o custo agora é baixo, adaptar o isolamento depois seria caro e arriscado, e autenticação e autorização corretas são uma das provas técnicas mais visíveis do projeto.

## Consequências

- **Positivas:** a demonstração pública funciona com vários usuários sem misturar dados.
- **Negativas:** toda consulta precisa filtrar por `user_id`, e um esquecimento vira vazamento.
- **Mitigação:** cada slice tem testes `test_user_cannot_access_another_users_*` (RNF-001, SEC-002).

## Mais informações

- [Modelo de dados](../arquitetura/modelo-de-dados.md) e [Segurança](../arquitetura/seguranca.md).
