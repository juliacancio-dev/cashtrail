# ADR-017 — E-mail transacional pelo Azure Communication Services

- **Status:** Aceita
- **Data:** 2026-10-08

## Contexto e problema

A recuperação de senha precisa enviar um link por e-mail. O serviço precisava caber na assinatura Azure e no orçamento. A Microsoft anunciou a aposentadoria do ACS Email para **2028-09-30**.

## Opções consideradas

1. **Azure Communication Services (ACS) Email**, com domínio gratuito do Azure.
2. **Provedor externo** (SendGrid, Resend etc.).
3. **SMTP** de um provedor de e-mail.

## Decisão

Escolhida: **ACS Email**, mesmo com a data de aposentadoria conhecida, porque fica na mesma nuvem e assinatura e atende o volume com folga. O envio passa por um adaptador plugável em `core/email.py` (`EMAIL_BACKEND=console` em desenvolvimento, `acs` em produção).

## Consequências

- **Positivas:** testado em produção em 2026-10-22 (o e-mail chegou e a troca de senha funcionou).
- **Negativas:** prazo de troca conhecido. **Trocar por SMTP antes de 2028-09-30**; o adaptador isola a mudança.

## Mais informações

- [Configuração do backend](../../backend/README.md#configuração) e [deploy](../guias/deploy-e-operacao.md#secrets-do-github).
