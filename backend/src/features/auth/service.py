from sqlalchemy.orm import Session

from src.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.features.auth import repository
from src.features.auth.models import User


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
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


def refresh_access_token(db: Session, refresh_token: str) -> str:
    try:
        user_id = decode_token(refresh_token, expected_type=TokenType.REFRESH)
    except InvalidTokenError:
        raise InvalidCredentialsError()

    user = repository.get_by_id(db, user_id)
    if user is None:
        raise InvalidCredentialsError()

    return create_access_token(user.id)
