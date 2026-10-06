from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.core import email
from src.core.config import settings
from src.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from src.features.auth import repository
from src.features.auth.models import User


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidResetTokenError(Exception):
    pass


def register_user(db: Session, email: str, password: str) -> User:
    if repository.get_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError(email)

    return repository.create_user(db, email=email, password_hash=hash_password(password))


def authenticate_user(db: Session, email: str, password: str) -> User:
    """RF-002: mensagem de erro deliberadamente genérica (nunca indica qual campo falhou)."""
    user = repository.get_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    return user


def issue_token_pair(user: User) -> tuple[str, str]:
    return create_access_token(user.id), create_refresh_token(user.id)


def token_predates_password_change(user: User, issued_at: datetime) -> bool:
    """RF-013: sessões abertas antes da última redefinição de senha deixam de valer.

    `iat` do JWT tem precisão de segundos, então compara com o segundo truncado.
    """
    if user.password_changed_at is None:
        return False
    return issued_at < user.password_changed_at.replace(microsecond=0)


def refresh_access_token(db: Session, refresh_token: str) -> str:
    try:
        user_id, issued_at = decode_token(refresh_token, expected_type=TokenType.REFRESH)
    except InvalidTokenError:
        raise InvalidCredentialsError()

    user = repository.get_by_id(db, user_id)
    if user is None or token_predates_password_change(user, issued_at):
        raise InvalidCredentialsError()

    return create_access_token(user.id)


def request_password_reset(db: Session, email_address: str) -> str | None:
    """RF-013: gera o token de redefinição. Retorna None se o e-mail não existe —
    o router responde igual nos dois casos para não revelar quais e-mails têm conta.
    """
    user = repository.get_by_email(db, email_address)
    if user is None:
        return None

    token, token_hash = generate_opaque_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.password_reset_token_expire_minutes)
    repository.create_password_reset_token(db, user.id, token_hash, expires_at, now)
    return token


def send_password_reset_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/reset-password?token={token}"
    email.send_email(
        to=to,
        subject="CashTrail - redefinição de senha",
        body=(
            "Recebemos um pedido para redefinir a sua senha no CashTrail.\n\n"
            f"Para criar uma nova senha, acesse: {link}\n\n"
            f"O link expira em {settings.password_reset_token_expire_minutes} minutos e só pode "
            "ser usado uma vez. Se você não pediu isso, ignore este e-mail."
        ),
    )


def reset_password(db: Session, token: str, new_password: str) -> None:
    reset_token = repository.get_password_reset_token_for_update(db, hash_opaque_token(token))
    now = datetime.now(timezone.utc)
    if reset_token is None or reset_token.used_at is not None or reset_token.expires_at <= now:
        raise InvalidResetTokenError()

    user = repository.get_by_id(db, reset_token.user_id)
    if user is None:
        raise InvalidResetTokenError()

    repository.reset_password(db, user, reset_token, hash_password(new_password), now)
