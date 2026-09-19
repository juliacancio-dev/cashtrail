"""Fixtures de teste compartilhadas (07-stack.md: Testcontainers com Postgres real).

Vive na raiz do backend (não em src/) porque é infraestrutura de teste transversal,
análoga ao core/ de produção — usada pelos testes de todas as slices.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.community.postgres import PostgresContainer

from src.core.database import Base, get_db
from src.main import app

# Importar os models de cada slice registra as tabelas em Base.metadata.
from src.features.accounts.models import Account  # noqa: F401
from src.features.auth.models import User  # noqa: F401
from src.features.budgets.models import Budget  # noqa: F401
from src.features.categories.models import Category  # noqa: F401
from src.features.goals.models import Goal  # noqa: F401
from src.features.recurring.models import RecurringTransaction  # noqa: F401
from src.features.transactions.models import Transaction  # noqa: F401


@pytest.fixture(scope="session")
def _postgres_container():
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def _engine(_postgres_container: PostgresContainer):
    url = _postgres_container.get_connection_url().replace("psycopg2", "psycopg")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(_engine):
    """Cada teste roda dentro de uma transação própria, revertida no final (isolamento)."""
    connection = _engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
