from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import InvalidTokenError, TokenType, decode_token
from src.features.auth import repository
from src.features.auth.models import User

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Dependency única de autenticação (ADR-004 / 08-architecture.md).

    Toda rota protegida deve depender exclusivamente desta função — nunca reimplementar
    a checagem de token em outro lugar.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credenciais invalidas ou ausentes",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        user_id = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    except InvalidTokenError:
        raise unauthorized

    user = repository.get_by_id(db, user_id)
    if user is None:
        raise unauthorized

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
