"""RF-013: recuperação de senha com token de uso único e expiração curta."""

import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from src.core import email
from src.core.security import hash_opaque_token
from src.features.auth.models import PasswordResetToken

PASSWORD = "supersecret1"
NEW_PASSWORD = "novasenha123"


@pytest.fixture
def sent_emails(monkeypatch):
    outbox: list[dict[str, str]] = []
    monkeypatch.setattr(
        email, "send_email", lambda to, subject, body: outbox.append({"to": to, "body": body})
    )
    return outbox


def _token_from(sent_email: dict[str, str]) -> str:
    link = next(word for word in sent_email["body"].split() if "reset-password?token=" in word)
    return parse_qs(urlparse(link).query)["token"][0]


def _register_and_request_reset(client, sent_emails, address: str) -> str:
    client.post("/auth/register", json={"email": address, "password": PASSWORD})
    client.post("/auth/forgot-password", json={"email": address})
    return _token_from(sent_emails[-1])


def test_forgot_password_sends_link_to_registered_email(client, sent_emails):
    client.post("/auth/register", json={"email": "forgot@example.com", "password": PASSWORD})

    response = client.post("/auth/forgot-password", json={"email": "forgot@example.com"})

    assert response.status_code == 202
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "forgot@example.com"
    assert _token_from(sent_emails[0])


def test_forgot_password_does_not_reveal_unregistered_email(client, sent_emails):
    client.post("/auth/register", json={"email": "exists@example.com", "password": PASSWORD})

    registered = client.post("/auth/forgot-password", json={"email": "exists@example.com"})
    unregistered = client.post("/auth/forgot-password", json={"email": "ghost@example.com"})

    assert registered.status_code == unregistered.status_code == 202
    assert registered.json() == unregistered.json()
    assert [e["to"] for e in sent_emails] == ["exists@example.com"]


def test_token_is_stored_only_as_hash(client, sent_emails, db_session):
    token = _register_and_request_reset(client, sent_emails, "hashonly@example.com")

    stored = db_session.query(PasswordResetToken).one()

    assert stored.token_hash == hash_opaque_token(token)
    assert stored.token_hash != token


def test_reset_password_changes_password(client, sent_emails):
    token = _register_and_request_reset(client, sent_emails, "reset@example.com")

    response = client.post("/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD})

    assert response.status_code == 204
    old_login = client.post("/auth/login", json={"email": "reset@example.com", "password": PASSWORD})
    new_login = client.post("/auth/login", json={"email": "reset@example.com", "password": NEW_PASSWORD})
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_reset_token_is_single_use(client, sent_emails):
    token = _register_and_request_reset(client, sent_emails, "singleuse@example.com")
    client.post("/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD})

    response = client.post("/auth/reset-password", json={"token": token, "new_password": "outrasenha99"})

    assert response.status_code == 400


def test_expired_reset_token_is_rejected(client, sent_emails, db_session):
    token = _register_and_request_reset(client, sent_emails, "expired@example.com")
    stored = db_session.query(PasswordResetToken).one()
    stored.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    response = client.post("/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD})

    assert response.status_code == 400


def test_new_request_invalidates_previous_token(client, sent_emails):
    first_token = _register_and_request_reset(client, sent_emails, "twice@example.com")
    client.post("/auth/forgot-password", json={"email": "twice@example.com"})
    second_token = _token_from(sent_emails[-1])

    first = client.post("/auth/reset-password", json={"token": first_token, "new_password": NEW_PASSWORD})
    second = client.post("/auth/reset-password", json={"token": second_token, "new_password": NEW_PASSWORD})

    assert first.status_code == 400
    assert second.status_code == 204


def test_unknown_reset_token_is_rejected(client):
    response = client.post(
        "/auth/reset-password", json={"token": "nao-existe", "new_password": NEW_PASSWORD}
    )

    assert response.status_code == 400


def test_reset_password_revokes_existing_sessions(client, sent_emails):
    """Um refresh/access token roubado antes da redefinição deixa de valer."""
    client.post("/auth/register", json={"email": "revoke@example.com", "password": PASSWORD})
    login = client.post("/auth/login", json={"email": "revoke@example.com", "password": PASSWORD})
    old_access_token = login.json()["access_token"]

    # iat do JWT tem precisão de segundos: garante que a redefinição acontece
    # num segundo posterior à emissão dos tokens antigos.
    time.sleep(1.1)
    client.post("/auth/forgot-password", json={"email": "revoke@example.com"})
    token = _token_from(sent_emails[-1])
    client.post("/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD})

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {old_access_token}"})
    refresh = client.post("/auth/refresh", headers={"X-Requested-With": "CashTrail"})

    assert me.status_code == 401
    assert refresh.status_code == 401


def test_reset_password_rejects_short_password(client, sent_emails):
    token = _register_and_request_reset(client, sent_emails, "short@example.com")

    response = client.post("/auth/reset-password", json={"token": token, "new_password": "curta"})

    assert response.status_code == 422
