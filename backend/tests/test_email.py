"""RF-013: adaptador de e-mail. O cliente real do Azure Communication Services é
substituído por um fake — o envio de verdade só dá para exercitar em produção."""

import logging

import pytest

from src.core import email
from src.core.config import settings
from src.features.auth import service


class FakeAcsClient:
    def __init__(self, fail: bool = False):
        self.sent: list[dict] = []
        self.fail = fail

    def begin_send(self, message: dict):
        if self.fail:
            raise RuntimeError("ACS indisponivel")
        self.sent.append(message)
        return type("Poller", (), {"result": lambda self: {"status": "Succeeded"}})()


@pytest.fixture
def acs_settings(monkeypatch):
    monkeypatch.setattr(settings, "email_backend", "acs")
    monkeypatch.setattr(settings, "acs_connection_string", "endpoint=https://x.communication.azure.com/;accesskey=k")
    monkeypatch.setattr(settings, "email_sender_address", "DoNotReply@abc.azurecomm.net")


def test_acs_backend_sends_expected_message(acs_settings, monkeypatch):
    client = FakeAcsClient()
    monkeypatch.setattr(email, "_build_acs_client", lambda: client)

    email.send_email("user@example.com", "Assunto", "Corpo do e-mail")

    assert client.sent == [
        {
            "senderAddress": "DoNotReply@abc.azurecomm.net",
            "recipients": {"to": [{"address": "user@example.com"}]},
            "content": {"subject": "Assunto", "plainText": "Corpo do e-mail"},
        }
    ]


@pytest.mark.parametrize("missing", ["acs_connection_string", "email_sender_address"])
def test_acs_backend_requires_connection_string_and_sender(acs_settings, monkeypatch, missing):
    monkeypatch.setattr(settings, missing, "")

    with pytest.raises(email.EmailConfigurationError):
        email.send_email("user@example.com", "a", "b")


def test_unknown_backend_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "email_backend", "pombo-correio")

    with pytest.raises(email.EmailConfigurationError):
        email.send_email("user@example.com", "a", "b")


def test_console_backend_does_not_need_azure(monkeypatch, caplog):
    monkeypatch.setattr(settings, "email_backend", "console")

    with caplog.at_level(logging.WARNING):
        email.send_email("user@example.com", "Assunto", "Corpo")

    assert "user@example.com" in caplog.text


def test_reset_email_failure_is_logged_without_leaking_the_token(acs_settings, monkeypatch, caplog):
    """Falha de envio roda em background depois do 202: não pode derrubar nada nem vazar o link."""
    monkeypatch.setattr(email, "_build_acs_client", lambda: FakeAcsClient(fail=True))

    with caplog.at_level(logging.ERROR):
        service.send_password_reset_email("user@example.com", "TOKEN-SECRETO-123")

    assert "falha ao enviar e-mail de redefinicao" in caplog.text
    assert "TOKEN-SECRETO-123" not in caplog.text
