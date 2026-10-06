"""Envio de e-mail transacional (RF-013).

Fica em core/ porque é um adaptador de integração externa, como database.py —
a slice auth decide *o que* enviar, este módulo decide *como*.
"""

import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    if settings.email_backend == "console":
        # Enquanto o Azure Communication Services não existir, o e-mail só aparece
        # no log do backend (Log stream do Container App em produção).
        logger.warning("E-mail (backend console) para %s | %s\n%s", to, subject, body)
        return

    raise ValueError(f"EMAIL_BACKEND desconhecido: {settings.email_backend!r}")
