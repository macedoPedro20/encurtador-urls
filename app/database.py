"""Configuração do banco de dados (SQLite por padrão, PostgreSQL em produção)."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def normalizar_url_banco(url: str) -> str:
    """Ajusta a URL do banco para o driver que usamos (psycopg 3).

    Plataformas como Render e Heroku entregam `postgres://...` ou `postgresql://...`,
    e o SQLAlchemy precisa de `postgresql+psycopg://...` para usar o driver certo.
    """
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


DATABASE_URL = normalizar_url_banco(os.getenv("DATABASE_URL", "sqlite:///./encurtador.db"))

if DATABASE_URL.startswith("sqlite"):
    # check_same_thread=False é necessário para SQLite com FastAPI (várias threads).
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping testa a conexão antes de usar: evita erro quando o banco
    # derrubou uma conexão ociosa (comum em planos gratuitos na nuvem).
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependência do FastAPI: abre uma sessão por requisição e fecha no final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
