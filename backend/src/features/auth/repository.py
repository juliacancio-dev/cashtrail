import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.features.auth.models import PasswordResetToken, User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, email: str, password_hash: str) -> User:
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_password_reset_token(
    db: Session, user_id: uuid.UUID, token_hash: str, expires_at: datetime, now: datetime
) -> None:
    # Só o link mais recente vale: pedidos anteriores ainda não usados são invalidados.
    db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user_id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )
    db.add(PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
    db.commit()


def get_password_reset_token_for_update(db: Session, token_hash: str) -> PasswordResetToken | None:
    # FOR UPDATE: duas requisições simultâneas com o mesmo token não conseguem
    # ambas passar pela checagem de "ainda não usado" (uso único de verdade).
    return db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash).with_for_update()
    )


def reset_password(
    db: Session, user: User, reset_token: PasswordResetToken, password_hash: str, now: datetime
) -> None:
    """Troca a senha e consome o token na mesma transação."""
    user.password_hash = password_hash
    user.password_changed_at = now
    reset_token.used_at = now
    db.commit()
