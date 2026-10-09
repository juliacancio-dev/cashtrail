"""As migrações reais (Alembic) aplicam num banco vazio e deixam o schema usável.

A suíte normal cria as tabelas com `Base.metadata.create_all`, então um erro SÓ da migração
(ex: valor de enum com a caixa errada, que o Postgres só rejeita no INSERT) passaria despercebido.
"""

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.features.accounts.models import Account, AccountType
from src.features.auth.models import User

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def migrated_url(_postgres_container):
    base_url = _postgres_container.get_connection_url().replace("psycopg2", "psycopg")
    name = f"migrations_{uuid.uuid4().hex[:8]}"
    admin = create_engine(base_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()

    url = base_url.rsplit("/", 1)[0] + "/" + name
    env = {**os.environ, "DATABASE_URL": url}
    for command in (["upgrade", "head"], ["check"]):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *command], cwd=BACKEND_DIR, env=env, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stdout + result.stderr
    return url


def test_every_account_type_can_be_stored_after_running_the_migrations(migrated_url):
    engine = create_engine(migrated_url)
    with Session(engine) as session:
        user = User(email="migration@example.com", password_hash="x")
        session.add(user)
        session.flush()
        for account_type in AccountType:
            session.add(Account(user_id=user.id, name=account_type.value, type=account_type))
        session.commit()

        stored = session.query(Account).filter_by(user_id=user.id).count()

    engine.dispose()
    assert stored == len(AccountType)
