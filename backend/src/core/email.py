"""Envio de e-mail transacional (RF-013).

Fica em core/ porque é um adaptador de integração externa, como database.py —
a slice auth decide *o que* enviar, este módulo decide *como*.
"""

import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmailConfigurationError(Exception):
    pass


def _build_acs_client():
    # Import tardio: dev/testes com backend "console" não precisam do SDK carregado.
    from azure.communication.email import EmailClient

    return EmailClient.from_connection_string(settings.acs_connection_string)


def _send_with_acs(to: str, subject: str, body: str) -> None:
    if not settings.acs_connection_string or not settings.email_sender_address:
        raise EmailConfigurationError(
            "EMAIL_BACKEND=acs exige ACS_CONNECTION_STRING e EMAIL_SENDER_ADDRESS"
        )

    message = {
        "senderAddress": settings.email_sender_address,
        "recipients": {"to": [{"address": to}]},
        "content": {"subject": subject, "plainText": body},
    }
    # begin_send só ENFILEIRA o e-mail; result() espera o serviço aceitar/recusar,
    # e levanta exceção se o envio falhar.
    _build_acs_client().begin_send(message).result()


def send_email(to: str, subject: str, body: str) -> None:
    if settings.email_backend == "console":
        # Enquanto o Azure Communication Services não existir, o e-mail só aparece
        # no log do backend (Log stream do Container App em produção).
        logger.warning("E-mail (backend console) para %s | %s\n%s", to, subject, body)
    elif settings.email_backend == "acs":
        _send_with_acs(to, subject, body)
    else:
        raise EmailConfigurationError(f"EMAIL_BACKEND desconhecido: {settings.email_backend!r}")
