"""Fixtures compartilhadas pelos testes.

Por padrão os testes usam SQLite em memória (rápido, sem dependências).
Para rodar contra outro banco, defina TEST_DATABASE_URL, por exemplo:

    TEST_DATABASE_URL=postgresql://usuario:senha@localhost:5432/teste pytest

O banco indicado deve ser descartável: as tabelas são criadas e apagadas a cada teste.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, normalizar_url_banco
from app.main import app


def _criar_engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        # SQLite em memória: um banco novo e isolado por teste.
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(normalizar_url_banco(url), pool_pre_ping=True)


@pytest.fixture()
def client():
    engine = _criar_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

    # Limpa o banco para o próximo teste (importa no PostgreSQL, que persiste).
    Base.metadata.drop_all(engine)
    engine.dispose()
